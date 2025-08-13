from decimal import Decimal
import datetime
import time
import math

from utils.calc import quantize
from utils.calc import percent_change
from utils.time_conversion import timestamp_to_datetime

import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)


class ExchangeState:
    def __init__(self, USD_holdings: Decimal, coin_holdings: Decimal, maker_fee: Decimal, taker_fee: Decimal):
        # Portfolio state
        self.USD_holdings = Decimal(USD_holdings)
        self.coin_holdings = Decimal(coin_holdings)
        self.maker_fee = Decimal(maker_fee) # Ideally this would be part of the config
        self.taker_fee = Decimal(taker_fee)

        # Initial conditions
        self.initial_portfolio_value = None
        self.initial_price = None
        self.initial_starting_timestamp = None

        # Market state
        self.current_price = None
        self.current_timestamp = None

        # Orders
        self.order_book = {}
        self.fulfilled_orders = {}
        self.current_order_number = 0

    def validate_exchange_state(self) -> None:
        """Validate that the current state values are present, numeric, and logical."""
        def validate_not_none_and_not_nan(name: str, value):
            if value is None:
                raise ValueError(f"{name} is None")
            if isinstance(value, (float, int)) and math.isnan(value):
                raise ValueError(f"{name} is NaN")

        # Check required fields
        validate_not_none_and_not_nan("current_price", self.current_price)
        validate_not_none_and_not_nan("current_timestamp", self.current_timestamp)
        validate_not_none_and_not_nan("USD_holdings", self.USD_holdings)
        validate_not_none_and_not_nan("coin_holdings", self.coin_holdings)

        # Logical value checks
        if self.USD_holdings < 0:
            logger.error(f"USD HOLDINGS: {self.USD_holdings}")
            raise ValueError("USD_holdings < 0")

        if self.coin_holdings < 0:
            logger.error(f"COIN HOLDINGS: {self.coin_holdings}")
            raise ValueError("coin_holdings < 0")

    def update_current_price_timestamp(self, current_price: float, timestamp: float) -> None:
        """Update the current market price and timestamp."""
        if current_price is None or math.isnan(current_price):
            raise ValueError("Invalid current_price: None or NaN")

        self.current_price = quantize(Decimal(current_price))
        self.current_timestamp = timestamp

        self.set_initial_conditions_if_first_iteration()


    def set_initial_conditions_if_first_iteration(self) -> None:
        """Initialize portfolio values and time tracking on the first iteration."""
        if self.initial_portfolio_value is not None:
            return

        self.initial_portfolio_value = self.coin_holdings * self.current_price + self.USD_holdings
        self.initial_price = self.current_price
        self.initial_starting_timestamp = self.current_timestamp

        self.current_read_time = self.current_timestamp
        self.start_read_time = time.time()

    def get_all_open_order_numbers(self):
        return list(self.order_book.keys())

    def update_coin_holdings(self, delta: Decimal) -> None:
        """Update coin holdings by a delta amount."""
        self.coin_holdings += delta
        self.coin_holdings = quantize(self.coin_holdings)

    def update_USD_holdings(self, delta: Decimal) -> None:
        """Update USD holdings by a delta amount."""
        self.USD_holdings += delta
        self.USD_holdings = quantize(self.USD_holdings)

    def get_USD_holdings(self) -> Decimal:
        """Get current USD holdings."""
        return self.USD_holdings

    def get_coin_holdings(self) -> Decimal:
        """Get current coin holdings."""
        return self.coin_holdings

    def get_USD_holds(self) -> Decimal:
        """Calculate the total USD currently on hold from all open orders."""
        return sum(order.USD_hold for order in self.order_book.values())

    def get_coin_holds(self) -> Decimal:
        """Calculate the total coin currently on hold from all open orders."""
        return sum(order.coin_hold for order in self.order_book.values())

    def get_USD_holdings_with_holds(self) -> Decimal:
        """Get total USD holdings including on-hold funds."""
        return self.get_USD_holdings() + self.get_USD_holds()

    def get_coin_holdings_with_holds(self) -> Decimal:
        """Get total coin holdings including on-hold funds."""
        return self.get_coin_holdings() + self.get_coin_holds()

    def current_portfolio_value(self) -> Decimal:
        """Calculate total portfolio value based on current market price."""
        return (
            self.get_coin_holdings_with_holds() * self.current_price
            + self.get_USD_holdings_with_holds()
        )
    
    def get_portfolio_percent_change_from_start(self) -> Decimal:
        return percent_change(self.current_portfolio_value(), self.initial_portfolio_value)

    def get_current_datetime(self) -> datetime:
        return timestamp_to_datetime(self.current_timestamp)

    def log_portfolio(self) -> None:
        USD_holdings = f"{self.get_USD_holdings():.2f}"
        USD_holds = f"{self.get_USD_holds():.2f}"
        coin_holdings = f"{self.get_coin_holdings():.8f}"
        coin_holds = f"{self.get_coin_holds():.8f}"
        logger.info(
            f"USD_holdings: ${USD_holdings} coin_holdings: {coin_holdings} "
            f"USD hold: ${USD_holds} Coin Hold: {coin_holds}"
        )

