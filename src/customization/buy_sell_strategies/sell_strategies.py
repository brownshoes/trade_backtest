from core.order.order import Order
from utils.calc import quantize


'''Completely sell off the open position'''
class MarketSell:
    def __init__(self):
        pass  # No initialization needed currently

    def create_sell_order(self, open_position, exits, trading_state, exg_state):
        order_number = exg_state.provide_order_number()
        
        # Calculate remaining coin amount to sell
        quantity = open_position.entry_quantity - open_position.quantity_sold
        quantity = quantize(quantity)

        sell_order = Order(
            order_number,
            "MARKET",
            "SELL",
            quantity,
            exg_state.taker_fee,
            exg_state.current_timestamp
        )
        return sell_order
