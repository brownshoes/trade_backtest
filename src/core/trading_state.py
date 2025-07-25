'''wrapper class that contains the state of the current trading environment'''
class TradingState:
    def __init__(self):
        self.open_positions = {}
        self.closed_positions = [] # list to preserve order of when position closed
        self.open_buy_orders = {}
        self.open_sell_orders = {}

    def get_string_positions_closed(self):
        result_string = ""
        for closed_position in self.closed_positions:
            result_string += closed_position.position.position_results_string()
        return result_string

    def get_string_positions_open(self):
        result_string = ""
        for open_position in self.open_positions:
            result_string += open_position.position_results_string()
        return result_string

    def open_orders_status(self):
        result_string = "Open Orders: #" + str(len(self.open_buy_orders) + len(self.open_sell_orders))
        for order_num, buy_info in self.open_buy_orders.items():
            result_string += "\n" + buy_info.order.order_string() + " " + str(buy_info.placed_time)

        for order_num, sell_info in self.open_sell_orders.items():
            result_string += "\n" + sell_info.order.order_string() + " " + str(sell_info.placed_time)

        return result_string

    def open_positions_status(self, current_price):
        result_string = "Open Positions: #" + str(len(self.open_positions))
        for order_num, open_position in self.open_positions.items():
            result_string += "\n " + open_position.position_status_string(current_price)
        return result_string