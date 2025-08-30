from datetime import datetime
import inspect

from core.exchange_state import ExchangeState
from core.position_tracking.trading_state import TradingState
from customization.conditions.entry_trade_conditions import OnlyOneOpenBuyCondition, OnlyOneOpenPositionEntryCondition
from core.trading import Trading
from core.strategy import Strategy
from core.time_series import TimeSeries
from core.series import Series
from core.limit_adjust import LimitAdjust
from core.order.order_completion import order_completion_factory
from core.clients.client_factory import client_factory

from utils.time_conversion import START_END_TIME_FORMAT


import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)


class Config:
    def __init__(
        self,
        # === Core Settings ===
        name: str,
        mode: str,
        trade: bool,
        start_time: str,
        end_time: str,

        # === Initial Holdings ===
        USD_holdings: float,
        coin_holdings: float,

        # === Fee Structure ===
        maker_fee: float,
        taker_fee: float,

        # === Timeframes ===
        time_series: list,
        main_time_series,
        exit_time_series,

        # === Strategy Components ===
        indicators: list,
        identify_entry: list,
        identify_exit: list,
        entry_trade_conditions: list,
        exit_trade_conditions: list,
        buy_strategy,
        sell_strategy,
        exit_strategy,

        # === Intake Fields ===
        csv_input_file = None

    ):
        # === Store Basic Configuration ===
        self.name = name
        self.mode = mode.upper()
        self.trade = trade
        self.start_time = start_time
        self.end_time = end_time
        self.USD_holdings = USD_holdings
        self.coin_holdings = coin_holdings
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee

        # === Timeframe Settings ===
        self.start_unix = datetime.strptime(start_time, START_END_TIME_FORMAT).timestamp()
        self.end_unix = datetime.strptime(end_time, START_END_TIME_FORMAT).timestamp()
        self.main_time_series = main_time_series
        self.exit_time_series = exit_time_series
        self.time_series = self.init_time_series(time_series)

        # === Inidcator/ Identify Components ===
        self.indicators = indicators
        self.identify_entry = identify_entry
        self.identify_exit = identify_exit

        # === Conditions ===
        default_entry_trade_conditions = [OnlyOneOpenBuyCondition(), OnlyOneOpenPositionEntryCondition()]
        self.entry_trade_conditions = entry_trade_conditions + default_entry_trade_conditions
        self.exit_trade_conditions = exit_trade_conditions

        # === Buy/Sell ===
        self.buy_strategy = buy_strategy
        self.sell_strategy = sell_strategy
        self.exit_strategy = exit_strategy

        # === Intake Fields ===
        self.csv_input_file = csv_input_file

        # === Time Series Assignment ===
        self.assign_time_series(self.indicators, self.time_series)
        self.assign_time_series(self.identify_entry, self.time_series)
        self.assign_time_series(self.identify_exit, self.time_series)

        self.main_time_series = self.resolve_time_series(main_time_series)
        self.exit_time_series = [self.resolve_time_series(ts_str) for ts_str in self.exit_time_series]


        # === State Initialization ===
        self.exg_state = ExchangeState(
            self.USD_holdings,
            self.coin_holdings,
            self.maker_fee,
            self.taker_fee
        )

        self.trading_state = TradingState()
        self.client = self.init_client(self.mode)
        self.limit_adjust = LimitAdjust()

        # === Trading System Setup ===
        self.strategy = Strategy(
            self.exit_time_series,
            self.entry_trade_conditions,
            self.exit_trade_conditions,
            self.identify_entry,
            self.identify_exit
        )

        self.trading = Trading(
            self.mode,
            self.strategy,
            self.trading_state,
            self.client,
            self.buy_strategy,
            self.sell_strategy,
            self.exit_strategy,
            self.main_time_series.candle_size,
            self.trade
        )

        # === Final Checks ===
        self.checks()

    def init_time_series(self, time_series_size):
        return [TimeSeries(candle_size=x) for x in time_series_size]

    def init_client(self, mode):
        order_completion = order_completion_factory(mode)
        return client_factory(mode, self.exg_state, None, order_completion)
    
    def resolve_time_series(self, ts_str: str) -> TimeSeries:
        ts_map = {ts.candle_size_str: ts for ts in self.time_series}
        ts = ts_map.get(ts_str)
        if not ts:
            raise ValueError(f"No TimeSeries found for '{ts_str}'")
        return ts
    
    def assign_time_series(self, objects, time_series_objs):
        ts_map = {ts.candle_size_str: ts for ts in time_series_objs}

        for obj in objects:
            ts_str = getattr(obj, 'time_series', None)
            if ts_str and isinstance(ts_str, str):
                matched_ts = ts_map.get(ts_str)
                if matched_ts:
                    obj.time_series = matched_ts

                    # Update any Series instances in the object's attributes
                    for attr_name in dir(obj):
                        attr = getattr(obj, attr_name)
                        # Check if attr is an instance of Series
                        # Assuming Series is imported or available in scope
                        if isinstance(attr, Series):
                            attr.time_series = matched_ts

                else:
                    obj_name = getattr(obj, 'name', None) or getattr(obj, 'id', None) or repr(obj)
                    logger.warning(
                        f"No TimeSeries found matching '{ts_str}' "
                        f"for object {obj_name} ({obj.__class__.__name__})"
                    )


    
    def checks(self):
        # Validate datetime format
        try:
            datetime.strptime(self.start_time, START_END_TIME_FORMAT)
            datetime.strptime(self.end_time, START_END_TIME_FORMAT)
        except ValueError:
            msg = (
                f"start_time and end_time must be in 'YYYY-MM-DD HH:MM' format. "
                f"Got: start_time='{self.start_time}', end_time='{self.end_time}'"
            )
            logger.error(msg)
            raise ValueError(msg)

        # Validate time_series is a list
        if not isinstance(self.time_series, list):
            msg = f"time_series must be a list, got: {type(self.time_series).__name__}"
            logger.error(msg)
            raise TypeError(msg)

        # Validate mode
        valid_modes = {"BACKTEST", "LIVE"}
        if self.mode not in valid_modes:
            msg = f"Invalid mode '{self.mode}'. Must be one of: {valid_modes}"
            logger.error(msg)
            raise ValueError(msg)


    def __str__(self):
        return self._stringify_config()

    def _stringify_config(self, indent=0):
        """
        Creates a string representation of the configuration, including nested objects.
        """
        indent_str = "  " * indent
        result = [f"{self.__class__.__name__}:"]
        
        for attr, value in self.__dict__.items():
            if attr.startswith("_"):
                continue  # Skip private/internal attributes

            value_str = self._stringify_value(value, indent + 1)
            result.append(f"{indent_str}  {attr}: {value_str}")

        return "\n".join(result)

    def _stringify_value(self, value, indent):
        """
        Stringify any value depending on type: primitive, object, or list.
        """
        indent_str = "  " * indent

        if isinstance(value, (str, int, float, bool, type(None))):
            return str(value)

        elif isinstance(value, list):
            if not value:
                return "[]"
            list_items = [
                f"\n{indent_str}- {self._stringify_value(item, indent + 1)}"
                for item in value
            ]
            return "".join(list_items)

        elif hasattr(value, '__dict__'):
            attrs = {
                k: v for k, v in value.__dict__.items()
                if not k.startswith("_") and not inspect.ismethod(v)
            }
            if not attrs:
                return f"{value.__class__.__name__}()"
            lines = [f"{value.__class__.__name__}:"]
            for k, v in attrs.items():
                val_str = self._stringify_value(v, indent + 1)
                lines.append(f"{indent_str}  {k}: {val_str}")
            return "\n".join(lines)

        else:
            return repr(value)