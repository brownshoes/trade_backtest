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

        #TODO MOVE TO trading????
        if(open_position.open_position_locked):
            existing_sell_order  = self.trading_state.open_sell_orders[open_position.sell_info_order_number] # TODO FIX WITH CORRECT ORDER #
            logger.error(
                f"Sell order already placed for Open Position\n"
                f"Position: {open_position.position_status_string(current_price)}\n"
                f"Sell order: {existing_sell_order .order_string()} | "
                f"Placed Time: {existing_sell_order.datetime}"
            )
            return False
        
        # TODO MOVE TO trading
        if sell_order is None:
            logger.error(f"Sell order failed to be created | Time: {current_datetime}")
            return False

        # TODO MOVE TO trading
        logger.info(
            f"Sell order created: {sell_order.order_string()} | Time: {current_datetime} | "
            f"Market Price: ${current_price:.2f}"
        )
        exg_state.log_portfolio()

        if self.client.place_order(sell_order):
            sell_order.set_order_placed(exg_state.current_timestamp, current_datetime, current_price)
            self.trading_state.open_sell_orders[sell_order.order_number] = sell_order

            open_position.lock_open_position(sell_order.order_number)

            logger.debug(self._generate_sell_debug_string(exg_state, sell_order))
            return True
        else:
            logger.error(f"Sell order failed to place: {sell_order.order_string()} | Time: {current_datetime}")
            return False

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

    def complete_sell_order(self, exg_state, sell_order):
        sell_order.percent_of_order_sold = Decimal(sell_order.order.execution_coin_amount / Decimal(sell_info.open_position.buy_info.order.execution_coin_amount))
        '''open_position needs to be updated first since the sell debug string contains information about the open_position.'''
        sell_info.open_position.update_open_position(sell_info)

        #update sell_info
        sell_info.usd_outcome = self._calculate_usd_outcome(sell_info)
        sell_info.percent_outcome = utils.percent_change(sell_info.order.execution_market_price, sell_info.open_position.buy_info.order.execution_market_price)
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
