from decimal import Decimal

from utils.calc import quantize, percent_of
from core.order.order import Order

'''Limit Exit. Set an exit upon a successful buy. Sell amount of coin at a set percent above market price at buy's execution time'''
class LimitExitPercentAbove:
    def __init__(self, percent_above_current_price):
        self.percent_above_current_price = Decimal(percent_above_current_price)

    def create_sell_order(self, open_position, exg_state):
        order_number = exg_state.provide_order_number()
        quantity = quantity = open_position.entry_quantity - open_position.quantity_sold
        quantity = quantize(quantity)

        execution_market_price = open_position.entry_price

        limit_price = Decimal(execution_market_price + percent_of(self.percent_above_current_price, execution_market_price))
        sell_order = Order(order_number, "LIMIT", "SELL", quantity, exg_state.maker_fee, exg_state.current_timestamp, limit_price)
        sell_order.allow_limit_adjust = False

        return sell_order