from decimal import Decimal
import time

from utils.calc import percent_change

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
            open_position.lock(sell_order)

            logger.debug(self._generate_sell_debug_string(exg_state, sell_order, open_position))
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
    
    def cancel_sell_order(self, sell_order, exg_state, open_position) -> bool:
        """
        Attempt to cancel a sell order. If partially filled, do not complete it yet—
        let trading logic resolve it when the position is closed out.
        """
        current_datetime = exg_state.get_current_datetime()
        logger.info(f"Cancelling sell order: {sell_order.order_string()} | Time: {current_datetime}")

        if not self.client.cancel_order(sell_order):
            logger.error(f"Cancel sell order failed: {sell_order.order_string()} | Time: {current_datetime}")
            return False

        if self._is_sell_order_executed(exg_state, sell_order.order_number):
            logger.warning(f"Sell order partially completed during cancel: {sell_order.order_string()} | Time: {current_datetime}")

            '''No need to complete the sell order immediately. Need to wait so that it is closed out by trading and an open_position is created'''
            # self.complete_sell_order(state_obj, sell_info)
        else:

            # Allow position to be attempted to be sold again
            open_position.unlock()
            del self.trading_state.open_sell_orders[sell_order.order_number]
            
            logger.info(f"Sell order successfully cancelled: {sell_order.order_string()} | Time: {current_datetime}")

        return True

    def _is_sell_order_executed(self, exg_state, order_number: str) -> bool:
        """Check if a buy order has been executed and is still open."""
        return (
            order_number in exg_state.fulfilled_orders and
            order_number in self.trading_state.open_sell_orders
        )

    '''Check if sell order executed.'''
    def check_and_complete_all_sell_orders(self, exg_state):
        completed_sell_orders = []

        # Use list() to allow safe deletion while iterating
        for order_number, sell_order in list(self.trading_state.open_sell_orders.items()):
            if self._is_sell_order_executed(exg_state, order_number):
                self.complete_sell_order(exg_state, sell_order)
                completed_sell_orders.append(sell_order)

        return completed_sell_orders

    def complete_sell_order(self, exg_state, sell_order):
        open_position = self.trading_state.get_open_position_by_sell_order(sell_order)

        '''open_position needs to be updated first since the sell debug string contains information about the open_position.'''
        open_position.record_sell(sell_order)
        sell_order.result_string = self._completed_sell_result_string(sell_order, exg_state, open_position)
        del self.trading_state.open_sell_orders[sell_order.order_number]
        open_position.unlock()

        logger.info(self._executed_sell_debug_string(sell_order))

        

    def _generate_sell_debug_string(self, exg_state, sell_order, open_position) -> str:
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
    
    def _executed_sell_debug_string(self, sell_order):
        debug_string = (
            f"\n #{sell_order.order_number} SELL EXECUTED ->"
            f"\n\t Placed Time: {sell_order.placed.datetime}"
            f"\n\t Placed Price: ${sell_order.placed.market_price:.2f}"
            f"\n Executed: ->"
            f"\n\t Time: {sell_order.execution.datetime}"
            f"\n\t Market Price: ${sell_order.execution.market_price:.2f}"
            f"\n\t USD: ${sell_order.execution.dollar_amount:.2f}"
            f"\n\t Coin: {sell_order.execution.coin_amount:.8f}"
            f"\n\t Fee: {sell_order.execution.fee:.8f}"
            f"\n\t Time To Execute: {sell_order.execution.time_to_execute} sec"
            f"\n\t Slippage: {sell_order.execution.price_difference:.2f} %"
            f"{sell_order.execution.price_difference_percent:.2f}"
            "\n-----------------------------------------------------------"
        )
        return debug_string

    
    '''
    Example:
    BUY: .1 coin @ 1000 = $100
    SELL: 25% of BUY @ $1015
        - %25 of .1 = .025          (.25 * .1 = .025)
        - .025 of $1015 = $25.375   (.025 * $1015 = $25.375)
    USD Outcome:
        SELL $ amount - (BUY $ Amount * % of BUY SOLD)
        Ex: $25.375 - ($100 * .25) = 0.375
    '''
    def _calculate_usd_outcome(self, buy_order, sell_order, percent_of_buy_sold):
        usd_outcome = Decimal(sell_order.execution.dollar_amount) - (
            Decimal(buy_order.execution.dollar_amount) * Decimal(percent_of_buy_sold)
        )
        return usd_outcome
    
    def _completed_sell_result_string(self, sell_order, exg_state, open_position):
        percent_sold = Decimal(sell_order.execution.coin_amount) / Decimal(open_position.buy_order.execution.coin_amount) * 100
        usd_outcome = self._calculate_usd_outcome(open_position.buy_order, sell_order, percent_sold / 100)
        percent_outcome = percent_change(
            sell_order.execution.market_price,
            open_position.buy_order.execution.market_price
        )
        total_position_percent_sold = open_position.percent_sold * 100
        
        result_string = "\n----------------------------------------------------"
        result_string += f"\n*Sell #: {open_position.times_sold}  ${usd_outcome:.2f}  % {percent_outcome:.2f}"
        result_string += f"\n*SELL Placed -> Time: {sell_order.placed.datetime}  MARKET: ${sell_order.placed.market_price:.2f}"
        result_string += f"\n*Executed: -> Time: {sell_order.execution.datetime}  MARKET: ${sell_order.execution.market_price:.2f}"
        result_string += (
            f"\n*Trade: ${sell_order.execution.dollar_amount:.2f}  <->  "
            f"Coin: {sell_order.execution.coin_amount:.8f}  Fee: ${sell_order.execution.fee:.2f}"
        )
        result_string += f"\n*Percent sold: %{percent_sold:.2f}  Total Position Sold: %{total_position_percent_sold:.2f}"
        result_string += (
            f"\n*Portfolio: ${exg_state.current_portfolio_value():.2f}  ->  "
            f"USD: ${exg_state.get_USD_holdings_with_holds():.2f}  "
            f"Coin: {exg_state.get_coin_holdings_with_holds():.2f}"
        )
        result_string += f"\n*DateTime: {exg_state.get_current_datetime()}"
        result_string += f"\n*Time To Execute: {sell_order.execution.time_to_execute} sec"
        result_string += (
            f"\n*Slippage: {sell_order.execution.price_difference:.2f} "
            f"%{sell_order.execution.price_difference_percent:.2f}"
        )

        return result_string