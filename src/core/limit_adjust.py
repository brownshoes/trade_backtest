import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)

class LimitAdjust:
    def __init__(self, mode, limit_order_duration_sec=3600):
        self.mode = mode
        self.limit_order_duration_sec = limit_order_duration_sec
        logger.info("Limit Adjust set to: " + str(self.limit_order_duration_sec) + " seconds")

    '''
    If previous market price was 38,000 and the limit price is set to be .1% lower, then .1% of 38,000 is 38. Limit buy price is 38,000 - 38 = 37,962
    Ex Price increase: 38,000 -> 38100
    Old limit price is: 37,962
    New limit price isL 38,061.9 (.1% of 38,100 is 38.1, new Limit Buy price is: 38,100 - 38.1 = 38,061.9)

    Ex Price decrease: 38,000 -> 37,980
    Old limit price is: 37,962
    New limit price is: 37,942.02 (.1% of 37980 = 37.98, new Limit Buy price is: 37,962 - 37.98 = 37,942.02)
    '''
    def adjust_limit_orders(self, place_buy, place_sell, exg_state, trading_state, buy_strategy, sell_strategy):
        open_order_nums = exg_state.get_all_open_order_numbers()
        for order_number in open_order_nums:
            order = exg_state.order_book[order_number]

            if(order.order_type != "LIMIT" or order.allow_limit_adjust == False):
                continue

            if(order.order_side == "BUY"):
                self._buy_limit_order_adjust(order, place_buy, exg_state, buy_strategy)

            elif(order.order_side == "SELL"):
                self._sell_limit_order_adjust(order, place_sell, exg_state, trading_state, sell_strategy)

    def _buy_limit_order_adjust(self, buy_order, place_buy, exg_state, buy_strategy):
        placed_market_price = buy_order.placed.market_price
        current_market_price = exg_state.current_price

        message = self._get_message(buy_order, exg_state, placed_market_price)

        # Cancel the order if it's past its allowed fill time
        if self._order_past_fill_time(buy_order.placed.timestamp, message, exg_state):
            #TODO CONVERT TO A MARKET BUY???, OR DON"T CANCEL IF NOT ENOUGH SLIPPAGE HAS OCCURED
            if place_buy.cancel_buy_order(buy_order, exg_state):
                logger.info(f"Cancelled stale BUY order {buy_order.order_string()} due to timeout.")
                return

        # Market price has DECREASED or stayed the same — no need to adjust
        if int(current_market_price) <= int(placed_market_price):
            logger.info(f"No Limit Adjust (price hasn't increased) for buy order {buy_order.order_number}:\n{message}")
            return

        logger.info("Limit order adjust: " + message)

        if place_buy.cancel_buy_order(buy_order, exg_state):
            new_order = buy_strategy.create_buy_order(None, None, exg_state)
            self._modify_new_order(buy_order, new_order, exg_state)

            buy_result = place_buy.place_buy_order(new_order, exg_state)

            # Retry on failure (only in live mode)
            if self.mode == "live" and not buy_result:
                logger.error(f"Buy order placement failed for new order {new_order.order_number}. Retrying...")
                buy_result = place_buy.place_buy_with_retries(new_order, None, None, exg_state, buy_strategy)

                if not buy_result:
                    logger.error("Buy retries FAILED. Order not placed!")

            return buy_result

        # If cancel failed
        logger.error(f"Limit order adjust: failed to cancel BUY order {buy_order.order_string()}")

    def _sell_limit_order_adjust(self, sell_order, place_sell, exg_state, trading_state, sell_strategy):
        placed_market_price = sell_order.placed.market_price
        current_market_price = exg_state.current_price
        open_position = trading_state.get_position_by_sell_order_number(sell_order.order_number)

        message = self._get_message(sell_order, exg_state, placed_market_price)

        '''Cancel the order if past its allowed fill time'''
        if self._order_past_fill_time(sell_order.placed.timestamp, message, exg_state):
            #TODO CONVERT TO A MARKET SELL, OR DON"T CANCEL IF NOT ENOUGH SLIPPAGE HAS OCCURED
            if(place_sell.cancel_sell_order(sell_order, exg_state)):
                logger.info(f"Cancelled stale SELL order {sell_order.order_string()} due to timeout.")
                return
        
        # Market price has INCREASED or stayed the same — no need to adjust
        if int(current_market_price) >= int(placed_market_price):
            logger.info(f"No Limit Adjust (price hasn't increased) for SELL order {sell_order.order_number}:\n{message}")
            return

        logger.info("Limit order adjust: " + message)

        if place_sell.cancel_sell_order(sell_order, exg_state):
            new_order = sell_strategy.create_sell_order(open_position, None, None, exg_state)
            self._modify_new_order(sell_order, new_order, exg_state)

            sell_result = place_sell.place_sell_order(new_order, exg_state, open_position)

            if self.mode == "live" and not sell_result:
                logger.error(f"Sell  order placement failed for new order {new_order.order_number}. Retrying...")
                sell_result = place_sell.place_sell_with_retries(new_order, open_position, None, None, exg_state, sell_strategy)

                if not sell_result:
                    logger.error("Sell retries FAILED. Order not placed!")

            return sell_result

        logger.error(f"Limit order adjust: failed to cancel SELL order {sell_order.order_string()}")

    def _order_past_fill_time(self, timestamp, message, exg_state):
        if(exg_state.current_timestamp >= timestamp + self.limit_order_duration_sec):
            logger.info(
                f"Limit order past allowed fill time of {self.limit_order_duration_sec} seconds.\n"
                f"{message}\n"
                f"\tOrder Timestamp: {timestamp}"
            )
            return True
        return False
    
    def _modify_new_order(self, order, new_order, exg_state):
        # Track old order numbers
        new_order.old_limit_order_numbers = order.old_limit_order_numbers
        new_order.old_limit_order_numbers.append(order.order_number)

        # Copy core order metadata
        new_order.creation_timestamp = order.creation_timestamp
        new_order.initial_limit_price = order.initial_limit_price

        # Adjust coin amount for partial buy fills
        if order.order_side == "BUY" and  order.execution is not None:
            logger.info(
                f"Buy order {order.order_number} partially filled. Adjusted new order amount: {new_order.quantity:.8f}"
            )
            new_order.quantity = order.quantity - order.execution.quantity

        # Log the modification
        new_order_string = self._create_new_order_string(order, new_order, exg_state)
        logger.info(new_order_string)


    def _get_message(self, order, exg_state, placed_price):
        return (
            f"{order.order_string()}\n"
            f"\tCurrent Time: {exg_state.get_current_datetime()}\n"
            f"\tCurrent Price: ${exg_state.current_price:.2f}\n"
            f"\tPlaced Price: ${int(placed_price)}"
        )
    
    def _create_new_order_string(self, order, new_order, exg_state):
        old_order_nums = ', '.join(map(str, new_order.old_limit_order_numbers))
        
        return (
            f"Limit order adjust:\n"
            f"\tOld: {order.order_string()}\n"
            f"\tNew: {new_order.order_string()}\n"
            f"\tTime: {exg_state.get_current_datetime()}\n"
            f"\tCurrent Price: ${exg_state.current_price:.2f}\n"
            f"\tPrevious order numbers: {old_order_nums}"
        )

