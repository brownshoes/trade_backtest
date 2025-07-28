from decimal import Decimal
import time

import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)


class PlaceSell:
    def __init__(self, trading_state, client):
        self.trading_state = trading_state
        self.client = client

        self.max_retries = 10

    def place_sell_order(self, sell_order, exg_state, open_position):
        current_datetime = exg_state.get_current_datetime()
        current_price = exg_state.current_price

        if self.client.place_order(sell_order):
            sell_order.set_order_placed(exg_state.current_timestamp, current_datetime, current_price)
            self.trading_state.open_sell_orders[sell_order.order_number] = sell_order

            #lock position with successfully placed(not executed) sell
            open_position.lock(sell_order)

            logger.debug(self._generate_sell_debug_string(exg_state, sell_order))
            return True
        else:
            logger.error(f"Sell order failed to place: {sell_order.order_string()} | Time: {current_datetime}")
            return False
        
    def place_sell_with_retries(self, original_order, open_position, strategies_sell, exits, exg_state, mode: str) -> bool:
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Attempting Sell Order attempt #{attempt}")

            # TODO look into. Updates the timestamp with the live timestamp
            if mode == "live":
                self.client.update_price_timestamp_api()

            try:
                sell_order = strategies_sell.create_sell_order(open_position, exits, self.trading_state, exg_state)
                if sell_order is None:
                    logger.warning("Sell order creation returned None.")
                    continue

                # Preserve original metadata
                sell_order.creation_timestamp = original_order.creation_timestamp
                sell_order.initial_limit_price = original_order.initial_limit_price

                if self.place_sell(sell_order, exg_state, open_position):
                    return True

            except Exception as e:
                logger.exception(f"Sell attempt #{attempt} failed with exception: {e}")

            # Exponential backoff
            time.sleep(0.25 * attempt)

        logger.error("All sell attempts failed.")
        return False
    
    def cancel_sell_order(self, order, exg_state, open_position) -> bool:
        """
        Attempt to cancel a sell order. If partially filled, do not complete it yet—
        let trading logic resolve it when the position is closed out.
        """
        current_datetime = exg_state.get_current_datetime()
        logger.info(f"Cancelling sell order: {order.order_string()} | Time: {current_datetime}")

        if not self.client.cancel_order(order):
            logger.error(f"Cancel sell order failed: {order.order_string()} | Time: {current_datetime}")
            return False

        if self._is_sell_order_executed(exg_state, order.order_number):
            logger.warning(f"Sell order partially completed during cancel: {order.order_string()} | Time: {current_datetime}")

            '''No need to complete the sell order immediately. Need to wait so that it is closed out by trading and an open_position is created'''
            # self.complete_sell_order(state_obj, sell_info)
        else:
            del self.trading_state.open_sell_orders[order.order_number]

            # Allow position to be attempted to be sold again
            open_position.unlock()
            
            logger.info(f"Sell order successfully cancelled: {order.order_string()} | Time: {current_datetime}")

        return True

    def _is_sell_order_executed(self, exg_state, order_number: str) -> bool:
        """Check if a buy order has been executed and is still open."""
        return (
            order_number in exg_state.fulfilled_orders and
            order_number in self.trading_state.open_sell_orders
        )

    '''Check if sell order executed.'''
    def check_open_sell_orders(self, exg_state):
        completed_sell_orders = []

        # Use list() to allow safe deletion while iterating
        for order_number, sell_order in list(self.trading_state.open_sell_orders.items()):
            if self._is_sell_order_executed(exg_state, order_number):
                self.complete_sell_order(exg_state, sell_order)
                completed_sell_orders.append(sell_order)

        return completed_sell_orders

    def check_and_complete_all_sell_orders(self, exg_state, sell_order):
        sell_order.percent_of_order_sold = Decimal(sell_order.order.execution_coin_amount / Decimal(sell_order.open_position.buy_info.order.execution_coin_amount))
        '''open_position needs to be updated first since the sell debug string contains information about the open_position.'''
        sell_info.open_position.update_open_position(sell_order)

        #update sell_info
        sell_info.result_string = self._completed_sell_result_string(sell_info, state_obj)
        self.completed_sell_orders_list.append(sell_info)

        #remove from open sells
        del self.open_sell_orders[sell_info.order_number]

        logger.info(self._executed_sell_debug_string(sell_info))



    def _generate_sell_debug_string(self, exg_state, open_position, sell_order) -> str:
        """
        Generates a debug string for a placed sell order using f-strings.
        """
        debug_string = (
            f"\n SELL PLACED -> #{open_position.buy_order.order_number} (Open Position)"
            f"\n\t Order Type: {sell_order.order_type}"
            f"\n\t Time: {exg_state.get_current_datetime()}"
            f"\n\t Market Price: ${exg_state.current_price:.2f}"
            f"\n\t Coin Amount: {sell_order.order_coin_amount:.8f}"
            f"\n\t Portfolio Value: ${exg_state.current_portfolio_value():.2f}"
            f"\n-----------------------------------------------------------"
        )
        return debug_string
