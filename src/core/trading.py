from core.place_buy import PlaceBuy
from core.place_sell import PlaceSell

import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)

class Trading:
    def __init__(self, mode, trading_state, client, strategies_buy, strategies_sell, strategies_exit=None, trade=False):
        self.mode = mode
        self.trading_state = trading_state
        self.strategies_buy = strategies_buy
        self.strategies_sell = strategies_sell
        self.strategies_exit = strategies_exit
        self.trade = trade

        self.placeBuy = PlaceBuy(trading_state, client)
        self.placeSell = PlaceSell(trading_state, client)

        self.log_trading()

    def execute_trading_strategy(self, exg_state, time_series_updated_list):
        self._execute_buy_logic(exg_state, time_series_updated_list)
        #self._execute_sell_logic(exg_state, time_series_updated_list)

    def check_open_orders_for_completion(self, exg_state):
        self._check_open_buy_orders(exg_state)
        #self._check_open_sell_orders(exg_state)

    def _check_open_buy_orders(self, exg_state):
        completed_buy_orders = self.placeBuy.check_and_complete_all_buy_orders(exg_state)

        for executed_buy_order in completed_buy_orders:
            self._open_position(executed_buy_order, exg_state)

    # def _check_open_sell_orders(self, exg_state):
    #     completed_sell_orders = self.placeSell.check_and_complete_all_sell_orders(exg_state)

    #     for order_num, open_position in list(self.trading_state.open_positions.items()):
    #         if open_position.percent_sold >= 0.999:
    #             self._close_position(open_position, exg_state)

    def _open_position(self, executed_buy_order, state_obj):
        open_position = OpenPosition(executed_buy_order)
        self.trading_state.open_positions[executed_buy_order.order_number] = open_position
        self._plot_open_close_position("green", state_obj)

        self._execute_strategy_exit(open_position, state_obj)

    '''Only executes one buy order per cycle'''
    def _execute_buy_logic(self, exg_state, time_series_updated_list):
        identified_entries = self.strategy.enter_position(self.trading_state, exg_state, time_series_updated_list)

        if not self.trade or not identified_entries:
            return 

        buy_order = self.strategies_buy.create_buy_order(identified_entries, self.trading_state, exg_state)
        result = self.placeBuy.place_buy_order(buy_order, exg_state)

        # Retry logic if initial placement fails (live mode)
        if self.mode == "live" and result is False:
            logger.error("Buy order failed to place. Attempting retries.")
            result = self.placeBuy.place_buy_with_retries(buy_order, identified_entries, exg_state, self.strategies_buy)
            if result is False:
                logger.error("Buy retries FAILED. Order not placed!")
                return

        #check if buy exectued immediately
        if result and self.placeBuy._is_buy_order_executed(exg_state, buy_order):
            self.placeBuy.complete_buy_order(exg_state, buy_order)
            self._open_position(buy_order, exg_state)

    def log_trading(self):
        trading_string = (
            f"Trading Configuration:\n"
            f"\tTrading: {self.trade}\n"
            f"\tstrategies_buy: {type(self.strategies_buy)}\n"
            f"\tstrategies_sell: {type(self.strategies_sell)}\n"
            f"\tstrategies_exit: {type(self.strategies_exit) if self.strategies_exit is not None else 'None'}\n"
        )
        logger.info(trading_string)
