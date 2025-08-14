from decimal import Decimal

from core.clients.client import Client
from core.order.order import Order

import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)

class BacktestClient(Client):
    def __init__(self, exg_state, order_completion, client_api=None):
        self.exg_state = exg_state
        #self.order_completion = order_completion
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
            # self.order_completion.complete_order(order, s)
            self.complete_order(order, s)
            self.fulfill_order(order)
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
            #self.order_completion.complete_order(order, s)
            self.complete_order(order, s)
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
    
    def complete_order(self, order, exg_state):
        current_price = exg_state.current_price

        #revert back to original funds
        order.restore_funds(exg_state)

        #Calculate fee for market and stop orders
        fee = order.quantity * current_price * order.fee_percentage

        '''If this is a limit buy, then we want to execute on the limit price, not the current market price'''
        execution_price = (
            order.limit_price if order.order_type == "LIMIT" else current_price
        )

        if order.order_side == "BUY":
            USD_change = 0 - (order.quantity * execution_price + fee)
            coin_change = order.quantity

        elif order.order_side == "SELL":
            USD_change = (order.quantity * execution_price) - fee
            coin_change = 0 - order.quantity

        # Update holdings on the state object
        exg_state.update_USD_holdings(USD_change)
        exg_state.update_coin_holdings(coin_change)

        # Record execution details using OrderExecution object
        execution_timestamp = exg_state.current_timestamp

        order.set_order_execution(
            timestamp = execution_timestamp,
            datetime = exg_state.get_current_datetime(),
            market_price = execution_price,
            dollar_amount = abs(USD_change),
            quantity = abs(coin_change),
            fee = fee,
            time_to_execute = execution_timestamp - order.creation_timestamp,
            price_difference = Decimal('0'),  # Could calculate based on initial price if needed
            price_difference_percent = Decimal('0'),
        )


