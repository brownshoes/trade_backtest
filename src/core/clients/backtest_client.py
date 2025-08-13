from core.clients.client import Client
from core.order.order import Order

import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)

class BacktestClient(Client):
    def __init__(self, exg_state, order_completion, client_api=None):
        self.exg_state = exg_state
        self.order_completion = order_completion
        self.client_api = client_api

    def place_order(self, order: Order) -> bool:
        s = self.exg_state  # shorthand for readability

        if not order.check_if_valid_order(s.current_price, s.USD_holdings, s.coin_holdings, s):
            logger.error(f"Unable to place order. Order invalid: {order.order_string()}")
            return False

        order.hold_funds(s)
        s.order_book[order.order_number] = order
        logger.info(f"Placed on order book: {order.order_string()}")

        if order.order_is_executable(s.current_price, s):
            self.order_completion.complete_order(order, s)
            s.fulfill_order(order)
        else:
            logger.debug(f"Order #{order.order_number} is not immediately executable: {order.order_string()}")

        return True

    def check_orders_for_execution(self):
        s = self.exg_state  # shorthand for readability

        executable_orders = []
        for order_number, order in s.order_book.items():
            if order.order_is_executable(s.current_price, s):
                executable_orders.append(order)

        for order in executable_orders:
            logger.info(f"Executing order: {order.order_string()}")
            self.order_completion.complete_order(order, s)
            self.fulfill_order(order)

        return executable_orders

    def fulfill_order(self, order: Order):
        s = self.exg_state  # shorthand for readability

        logger.info(f"Order filled: {order.order_string()} Time: {s.get_current_datetime()}")

        s.fulfilled_orders[order.order_number] = order
        del s.order_book[order.order_number]

    def cancel_order(self, order: Order):
        s = self.exg_state  # shorthand for readability

        if order.order_number not in s.order_book:
            logger.error(f"Cancel Error: Order not in order book: {order.order_string()} Time: {s.get_current_datetime()}")
            return False

        # Restore portfolio funds
        order.restore_funds(s)
        del s.order_book[order.order_number]
        logger.info(f"Order removed/cancelled from order book: {order.order_string()} Time: {s.get_current_datetime()}")
        return True


