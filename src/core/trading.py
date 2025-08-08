from core.place_buy import PlaceBuy
from core.place_sell import PlaceSell

from core.position_tracking.open_position import OpenPosition
from core.position_tracking.closed_position import ClosedPosition
from core.position_tracking.statistics import Statistics


import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)

class Trading:
    def __init__(self, mode, trading_state, client, buy_strategy, sell_strategy, 
                 exit_strategy=None, stats_candle_size=15, trade=False):
        self.mode = mode
        self.trading_state = trading_state
        self.buy_strategy = buy_strategy
        self.sell_strategy = sell_strategy
        self.exit_strategy = exit_strategy
        self.stats_candle_size = stats_candle_size
        self.trade = trade

        self.placeBuy = PlaceBuy(trading_state, client)
        self.placeSell = PlaceSell(trading_state, client)

        self.trade_num = 0

        self.log_trading()

    def execute_trading_strategy(self, exg_state, time_series_updated_list):
        self._execute_buy_logic(exg_state, time_series_updated_list)
        self._execute_sell_logic(exg_state, time_series_updated_list)

    def check_open_orders_for_completion(self, exg_state):
        self._check_open_buy_orders(exg_state)
        self._check_open_sell_orders(exg_state)

    def _check_open_buy_orders(self, exg_state):
        buy_trade_overviews = self.placeBuy.check_and_complete_all_buy_orders(exg_state)

        for trade_overview_buy in buy_trade_overviews:
            open_position = self._open_position(trade_overview_buy, exg_state)

            self._execute_strategy_exit(open_position, exg_state)

    def _check_open_sell_orders(self, exg_state):
        sell_trade_overviews = self.placeSell.check_and_complete_all_sell_orders(exg_state)

        for sell_trade_overview in sell_trade_overviews:
            # Record the sell in the OpenPosition
            open_position = self.trading_state.get_position_by_sell_order_number(sell_trade_overview.order_number)
            trade_result = open_position.record_sell()
            logger.info(trade_result)

        for order_num, open_position in list(self.trading_state.open_positions.items()):
            if open_position.percent_sold >= 0.999:
                self._close_position(open_position, exg_state)

    def _open_position(self, trade_overview_buy):
        self.trade_num += 1
        open_position = OpenPosition(trade_overview_buy, self.trade_num)
        self.trading_state.add_open_position(open_position)


    def _close_position(self, open_position):
        closed_position = ClosedPosition(open_position)
        self.trading_state.add_closed_position(ClosedPosition(open_position))

        statistics = Statistics(self.trading_state, self.stats_candle_size)

        logger.info(closed_position.summary())
        logger.info(statistics.summary_string_color())

    '''Only executes one buy order per cycle'''
    def _execute_buy_logic(self, exg_state, time_series_updated_list):
        identified_entries = self.strategy.enter_position(self.trading_state, exg_state, time_series_updated_list)

        if not self.trade or not identified_entries:
            return 

        buy_order = self.buy_strategy.create_buy_order(identified_entries, self.trading_state, exg_state)
        result = self._place_buy_order.place_buy_order(buy_order, exg_state)

        # Retry logic if initial placement fails (live mode)
        if self.mode == "live" and result is False:
            logger.error("Buy order failed to place. Attempting retries.")
            result = self.placeBuy.place_buy_with_retries(buy_order, identified_entries, exg_state, self.buy_strategy)
            if result is False:
                logger.error("Buy retries FAILED. Order not placed!")
                return

        #check if buy exectued immediately
        if result and self.placeBuy._is_buy_order_executed(exg_state, buy_order):
            self.placeBuy.complete_buy_order(exg_state, buy_order)
            self._open_position(buy_order, exg_state)

    def _execute_sell_logic(self, exg_state, time_series_updated_list) -> bool:
        """
        Sell everything if strategy indicates, otherwise check if individual positions should close.
        First, attempt to cancel any open positions. Then, place new sell orders for the rest.
        """
        positions_to_close = self.strategy.exit_positions(self.trading_state, exg_state, time_series_updated_list)
        success = True
        valid_positions = {}

        if not self.trade:
            return success

        # Step 1: Cancel any existing sells that were placed by a strategy_exit for this open_position
        for open_position, exits in positions_to_close.items():
            if open_position.is_locked:
                cancel_result = self.placeSell.cancel_sell_order(open_position.sell_order, exg_state)

                if not cancel_result:
                    logger.error(
                        f"Failed to cancel open sell order: {open_position.sell_order.order_string()} "
                        f"for buy_order: {open_position.buy_order.order_string()}"
                    )
                    success = False
                    continue
            # Either unlocked or successfully cancelled
            valid_positions[open_position] = exits

        # Step 2: Process sell logic for positions we can act on
        for open_position, exits in valid_positions.items():
            sell_order = self.sell_strategy.create_sell_order(open_position, exits, self.trading_state, exg_state)
            result = self._place_sell_order(sell_order, exg_state, open_position)

            # Retry logic in live mode
            if self.mode == "live" and result is False:
                logger.error("Sell order failed to place. Attempting retries.")
                result = self.placeSell.place_sell_with_retries(
                    original_order=sell_order,
                    open_position=open_position,
                    sell_strategy=self.sell_strategy,
                    exits=exits,
                    exg_state=exg_state,
                    mode=self.mode
                )
                if not result:
                    logger.error("Sell retries FAILED. Order not placed!")
                    success = False
                    continue

            # Check if the sell was executed immediately
            if result and self.placeSell.check_if_sell_order_executed(exg_state, sell_order):
                self._check_open_sell_orders(exg_state)

        return success
    
    def _execute_strategy_exit(self, open_position, exg_state):
        if(self.exit_strategy != None and self.trade):
            logger.info("Executing Strategy Exit")
            sell_order = self.exit_strategy.create_sell_order(open_position, exg_state)   

            self.placeSell.place_sell_order(sell_order, exg_state, open_position)

    def _place_buy_order(self, buy_order, exg_state):
        current_datetime = exg_state.get_current_datetime()
        current_price = exg_state.current_price
    
        if buy_order is None:
            logger.error(f"Buy order failed to be created | Time: {current_datetime}")
            return False

        logger.info(
            f"Buy order created: {buy_order.order_string()} | Time: {current_datetime} | "
            f"Market Price: ${current_price:.2f}"
        )

        exg_state.log_portfolio()

        result = self.placeBuy.place_buy_order(buy_order, exg_state)

        if not result:
            logger.error(f"Buy order failed to place: {buy_order.order_string()} Time: {current_datetime}")

        return result

    def _place_sell_order(self, sell_order, exg_state, open_position):
        current_datetime = exg_state.get_current_datetime()
        current_price = exg_state.current_price

        if open_position.is_locked:
            existing_sell_order  = self.trading_state.open_sell_orders[open_position.sell_order.order_number]
            logger.error(
                f"Sell order already placed for Open Position\n"
                f"Position: {open_position.position_status_string(current_price)}\n"
                f"Sell order: {existing_sell_order .order_string()} | "
                f"Placed Time: {existing_sell_order.datetime}"
            )
            return False
        
        if sell_order is None:
            logger.error(f"Sell order failed to be created | Time: {current_datetime}")
            return False

        logger.info(
            f"Sell order created: {sell_order.order_string()} | Time: {current_datetime} | "
            f"Market Price: ${current_price:.2f}"
        )
        exg_state.log_portfolio()

        result = self.placeSell.place_sell(sell_order, exg_state, open_position)

        if(result == False):
            logger.error(f"Sell order failed to place: {sell_order.order_string()} Time: {current_datetime}")

        return result

    def log_trading(self):
        trading_string = (
            f"Trading Configuration:\n"
            f"\tTrading: {self.trade}\n"
            f"\tbuy_strategy: {type(self.buy_strategy)}\n"
            f"\tsell_strategy: {type(self.sell_strategy)}\n"
            f"\texit_strategy: {type(self.exit_strategy) if self.exit_strategy is not None else 'None'}\n"
        )
        logger.info(trading_string)
