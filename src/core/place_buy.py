import time

from core.position_tracking.trade_data import TradeOverview

import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)


class PlaceBuy:
    def __init__(self, trading_state, client):
        self.trading_state = trading_state
        self.client = client

        self.max_retries = 10
    
    def place_buy_order(self, buy_order, exg_state):
        current_datetime = exg_state.get_current_datetime()
        current_price = exg_state.current_price

        if self.client.place_order(buy_order):
            buy_order.set_order_placed(exg_state.current_timestamp, current_datetime, current_price)
            self.trading_state.open_buy_orders[buy_order.order_number] = buy_order
            logger.debug(self._generate_buy_debug_string(exg_state, buy_order))
            return True
        else:
            logger.error(f"Buy order failed to place: {buy_order.order_string()} | Time: {current_datetime}")
            return False


    def place_buy_with_retries(self, original_order, identified_entries, strategies_buy, exg_state, mode: str) -> bool:
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Attempting Buy Order attempt #{attempt}")

            # TODO look into. Updates the timestamp with the live timestamp
            if mode == "live":
                self.client.update_price_timestamp_api()

            try:
                buy_order = strategies_buy.create_buy_order(identified_entries, self.trading_state, exg_state)
                if buy_order is None:
                    logger.warning("Buy order creation returned None.")
                    continue

                # Preserve original metadata
                buy_order.creation_timestamp = original_order.creation_timestamp
                buy_order.initial_limit_price = original_order.initial_limit_price

                if self.place_buy(buy_order, exg_state):
                    return True

            except Exception as e:
                logger.exception(f"Buy attempt #{attempt} failed with exception: {e}")

            # Exponential backoff
            time.sleep(0.25 * attempt)

        logger.error("All buy attempts failed.")
        return False
    
    def cancel_buy_order(self, order, exg_state) -> bool:
        """
        Attempt to cancel a buy order. If partially filled, do not complete it yet—
        let trading logic resolve it when the position is closed out.
        """
        current_datetime = exg_state.get_current_datetime()
        logger.info(f"Cancelling buy order: {order.order_string()} | Time: {current_datetime}")

        if not self.client.cancel_order(order):
            logger.error(f"Cancel buy order failed: {order.order_string()} | Time: {current_datetime}")
            return False

        if self._is_buy_order_executed(exg_state, order.order_number):
            logger.warning(f"Buy Order partially completed during cancel: {order.order_string()} | Time: {current_datetime}")

            '''No need to complete the Buy order immediately. Need to wait so that it is closed out by trading and an open_position is created'''
            # self.complete_buy_order(state_obj, buy_info)
        else:
            del self.trading_state.open_buy_orders[order.order_number]
            logger.info(f"Buy order successfully cancelled: {order.order_string()} | Time: {current_datetime}")

        return True


    def _is_buy_order_executed(self, exg_state, order_number: str) -> bool:
        """Check if a buy order has been executed and is still open."""
        return (
            order_number in exg_state.fulfilled_orders and
            order_number in self.trading_state.open_buy_orders
        )

    '''Check if buy order executed.'''
    def check_and_complete_all_buy_orders(self, exg_state):
        trade_overviews = []

        # Use list() to allow safe deletion while iterating
        for order_number, buy_order in list(self.trading_state.open_buy_orders.items()):
            if self._is_buy_order_executed(exg_state, order_number):
                trade_overview = self.complete_buy_order(buy_order)
                trade_overviews.append(trade_overview)

        return trade_overviews

    def complete_buy_order(self, buy_order):
        del self.trading_state.open_buy_orders[buy_order.order_number]

        trade_overview = TradeOverview(buy_order)
        logger.info(trade_overview)

        return trade_overview


    def _generate_buy_debug_string(self, exg_state, buy_order):
        return (
            f"\nBUY PLACED:-> {buy_order.order_string()}"
            f"\n\tOrder Type: {buy_order.order_type}"
            f"\n\tTime: {exg_state.get_current_datetime()}"
            f"\n\tMarket Price: ${exg_state.current_price:.2f}"
            f"\n\tCoin Amount: {buy_order.order_quantity:.8f}"
            f"\n\tPortfolio Value: ${exg_state.current_portfolio_value():.2f}"
        )

