from datetime import datetime

from core.exchange_state import ExchangeState
from core.position_tracking.trading_state import TradingState
from core.trading import Trading
from core.time_series import TimeSeries
from core.order.order_completion import order_completion_factory
from core.clients.client_factory import client_factory

from utils.time_conversion import START_END_TIME_FORMAT


import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)


class Config:
    def __init__(
        self,
        mode: str,
        trade,
        start_time,
        end_time,
        USD_holdings: float,
        coin_holdings: float,
        maker_fee: float,
        taker_fee: float,
        time_series,
        main_time_series,
        indicators,
        strategies_buy,
        strategies_sell,
        strategies_exit,
        **extra_fields
    ):
        self.mode = mode.upper()
        self.trade = trade
        self.start_time = start_time
        self.end_time = end_time
        self.USD_holdings = USD_holdings
        self.coin_holdings = coin_holdings
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee

        self.indicators = indicators

        self.strategies_buy = strategies_buy
        self.strategies_sell = strategies_sell
        self.strategies_exit = strategies_exit

        self.extra_fields = extra_fields

        self.exg_state = ExchangeState(
            self.USD_holdings,
            self.coin_holdings,
            self.maker_fee,
            self.taker_fee
        )

        self.trading_state = TradingState()

        self.time_series = self.init_time_series(time_series)
        self.client = self.init_client(self.mode)

        self.trading = Trading(self.mode, self.trading_state, self.client, self.strategies_buy, self.strategies_sell, 
                 main_time_series.candle_size, self.strategies_exit, self.trade)

        # Dynamically set any extra config fields
        for key, value in extra_fields.items():
            setattr(self, key, value)

        self.checks()

    def init_time_series(self, time_series_size):
        return [TimeSeries(candle_size=x) for x in time_series_size]

    def init_client(self, mode):
        order_completion = order_completion_factory(mode)
        return client_factory(mode, self.exg_state, None, order_completion)

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


    def to_string(self):
        return self._build_string(self)

    def _build_string(self, obj, indent=0):
        pad = "  " * indent
        lines = []

        if isinstance(obj, dict):
            if not obj:
                lines.append(f"{pad}(empty dict)")
            else:
                for key, value in obj.items():
                    lines.append(f"{pad}{key}:")
                    lines.append(self._build_string(value, indent + 1))

        elif isinstance(obj, list):
            if not obj:
                lines.append(f"{pad}(empty list)")
            else:
                for i, item in enumerate(obj):
                    lines.append(f"{pad}- [{i}]:")
                    lines.append(self._build_string(item, indent + 1))

        elif hasattr(obj, '__dict__'):
            attrs = vars(obj)
            if not attrs:
                lines.append(f"{pad}{obj}")
            else:
                for key, value in attrs.items():
                    lines.append(f"{pad}{key}:")
                    lines.append(self._build_string(value, indent + 1))

        else:
            lines.append(f"{pad}{obj}")

        return "\n".join(lines)

def print_config(self) -> str:
    def format_obj(obj, indent=2, seen=None):
        if seen is None:
            seen = {}

        pad = ' ' * indent
        lines = []

        obj_id = id(obj)
        if obj_id in seen:
            lines.append(f"{pad}<{seen[obj_id]}>")
            return lines

        if isinstance(obj, (str, int, float, bool, type(None))):
            lines.append(f"{pad}{obj}")
            return lines

        seen[obj_id] = type(obj).__name__

        if isinstance(obj, dict):
            for key, value in obj.items():
                lines.append(f"{pad}{key}:")
                lines.extend(format_obj(value, indent + 2, seen))
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                lines.append(f"{pad}-")
                lines.extend(format_obj(item, indent + 2, seen))
        else:
            # Handle dynamic or unknown object fields
            attributes = {
                k: v for k, v in vars(obj).items()
                if not k.startswith("_") and not callable(v)
            }

            for attr, value in attributes.items():
                lines.append(f"{pad}{attr}:")
                lines.extend(format_obj(value, indent + 2, seen))

        return lines

    header = f"{self.__class__.__name__}:"
    body = format_obj(self, indent=2)
    return "\n".join([header] + body)
