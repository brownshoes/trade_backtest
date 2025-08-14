from decimal import Decimal
from core.order.order_classes import OrderPlaced
from core.order.order_classes import OrderExecution

from utils.calc import quantize

import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)

class Order:
    def __init__(
        self,
        order_number: int,
        order_type: str,       # "MARKET" or "LIMIT""
        order_side: str,       # "BUY" or "SELL"
        quantity: Decimal,
        fee_percentage: Decimal,
        creation_timestamp: str,
        limit_price: Decimal = None,
        allow_limit_adjust: bool = False
    ):
        '''Order creation'''
        self.order_number = order_number
        self.order_type = order_type
        self.order_side = order_side
        self.quantity = quantity
        self.fee_percentage = fee_percentage
        self.creation_timestamp = creation_timestamp

        '''Limit orderss'''
        self.limit_price = limit_price
        self.initial_limit_price = limit_price
        self.old_limit_order_numbers = [] # limit order history tracking
        self.allow_limit_adjust: bool = allow_limit_adjust #Want the option to sell immediately or turn off for testing

        '''Order placed - set to None until order placed'''
        self.placed = None

        '''Order execution - set to None until executed'''
        self.execution = None

        '''API trade JSON'''
        self.order_trade_data = None
        self.order_trade_id = None

        '''Holding'''
        self.USD_hold: Decimal = Decimal(0)
        self.coin_hold: Decimal = Decimal(0)

        ''' Parameter check'''
        self._validate_order_fields()

    def _validate_order_fields(self):
        valid_types = {"MARKET", "LIMIT"}
        valid_sides = {"BUY", "SELL"}

        # Validate type
        if self.order_type not in valid_types:
            raise ValueError(f"Invalid order_type: '{self.order_type}'.")

        # Validate side
        if self.order_side not in valid_sides:
            raise ValueError(f"Invalid order_side: '{self.order_side}'.")

        # Validate coin amount
        if not isinstance(self.quantity, Decimal):
            raise TypeError("quantity must be a Decimal.")

        if not self.quantity.is_finite() or self.quantity <= 0:
            raise ValueError(
                f"Invalid quantity: {self.quantity}. Must be > 0 and finite."
            )

        # Validate required price fields for LIMIT
        if self.order_type == "LIMIT" and self.limit_price is None:
            raise ValueError("LIMIT orders require a limit_price.")
        

    '''check if holdings allow trade. #Market order uses market price'''
    def _validate_holdings(self, current_price: Decimal, USD_holdings: Decimal, coin_holdings: Decimal, exg_state) -> bool:
        # Determine trade value in USD
        if self.order_type == "MARKET":
            USD_trade_value = self.quantity * current_price
        else:
            USD_trade_value = self.quantity * self.limit_price

        # Quantize for consistent precision (e.g., 9 decimal places)
        USD_trade_value = USD_trade_value.quantize(Decimal('1.000000000'))

        if self.order_side == "BUY":
            if USD_holdings >= USD_trade_value:
                return True
            else:
                logger.error(
                    f"Validate holdings failed for BUY: USD holdings {USD_holdings} < "
                    f"required trade value {USD_trade_value} at {exg_state.get_current_datetime()}"
                )
                raise ValueError("Insufficient USD holdings for BUY order.")

        elif self.order_side == "SELL":
            if coin_holdings >= self.quantity:
                return True
            else:
                logger.error(
                    f"Validate holdings failed for SELL: coin holdings {coin_holdings} < "
                    f"order coin amount {self.quantity} at {exg_state.get_current_datetime()}"
                )
                raise ValueError("Insufficient coin holdings for SELL order.")

        return False

    def check_if_valid_order(self, current_price, USD_holdings, coin_holdings, exg_state):
        return (
            self._validate_holdings(current_price, USD_holdings, coin_holdings, exg_state)
            and self._validate_market_conditions(current_price, exg_state)
        )
        

    '''Validate if market conditions allow for placing the order'''
    def _validate_market_conditions(self, current_price: Decimal, exg_state) -> bool:
        if self.order_type == "MARKET":
            return True

        if self.order_type == "LIMIT":
            if self.order_side == "BUY" and self.limit_price < current_price:
                return True
            if self.order_side == "SELL" and self.limit_price > current_price:
                return True

        logger.error(
            f"Market condition validation failed for Order #{self.order_number}.\n"
            f"\tLimit Price: ${self.limit_price:.2f}, Current Price: ${current_price:.2f}\n"
            f"\tType: {self.order_type}, Side: {self.order_side}, Time: {exg_state.get_current_datetime()}"
        )
        return False

        
    '''Check if the order is currently executable based on market conditions.'''
    def order_is_executable(self, current_price: Decimal, exg_state) -> bool:
        if self.order_type == "MARKET":
            return True
        
        info_string = (
            f"Order #{self.order_number} not currently executable.\n"
            f"\tCurrent Market Price: ${round(current_price, 2)}\n"
            f"\tLimit Price: ${round(self.limit_price, 2)}\n"
            f"\tOrder Type: {self.order_type}, Side: {self.order_side}\n"
            f"\tCurrent Time: {exg_state.get_current_datetime()}"
        )

        if self.order_side == "BUY" and current_price > self.limit_price:
            logger.debug(info_string + "\n\tMarket price is higher than limit buy price.")
            return False

        if self.order_side == "SELL" and current_price < self.limit_price:
            logger.debug(info_string + "\n\tMarket price is lower than limit sell price.")
            return False

        return True

    def hold_funds(self, exg_state):
        """
        Gemini holds the fee in USD for BUY orders (fee added to the hold).
        For SELL orders, only the coin amount is held and the fee is subtracted on sell execution.
        """
        if self.order_side == "BUY":
            # Calculate USD to hold based on order type
            if self.order_type == "LIMIT":
                USD_hold = self.limit_price * self.quantity
            else:  # MARKET order
                USD_hold = exg_state.current_price * self.quantity

            fee = USD_hold * self.fee_percentage
            self.USD_hold = USD_hold + fee

            logger.info(
                f"Holding funds for BUY order #{self.order_number} -> "
                f"USD_hold: ${quantize(USD_hold)}, "
                f"Expected Fee: ${quantize(fee)}, "
                f"Total Hold: ${quantize(self.USD_hold)}"
            )

            # Update USD holdings in state (subtract held funds)
            exg_state.update_USD_holdings(-self.USD_hold)

        elif self.order_side == "SELL":
            self.coin_hold = self.quantity

            logger.info(
                f"Holding funds for SELL order #{self.order_number} -> "
                f"Coin_hold: {self.coin_hold}"
            )

            # Update coin holdings in state (subtract held coins)
            exg_state.update_coin_holdings(-self.quantity)

    def restore_funds(self, exg_state):
        if self.order_side == "BUY":
            exg_state.update_USD_holdings(self.USD_hold)
            self.USD_hold = Decimal(0)

        elif self.order_side == "SELL":
            exg_state.update_coin_holdings(self.coin_hold)
            self.coin_hold = Decimal(0)

    def set_order_placed(self,         
            timestamp: float,
            datetime: str,
            market_price: Decimal
    ):
        self.placed = OrderPlaced(timestamp, datetime, market_price)

    def set_order_execution(self,
        timestamp: float,
        datetime: str,
        market_price: Decimal,
        dollar_amount: Decimal,
        quantity: Decimal,
        fee: Decimal,
        time_to_execute: float,
        price_difference: Decimal,
        price_difference_percent: Decimal,
    ):
        self.execution = OrderExecution(
            timestamp,
            datetime,
            market_price,
            dollar_amount,
            quantity,
            fee,
            time_to_execute,
            price_difference,
            price_difference_percent,
        )


    def order_string(self) -> str:
        info = (
            f"# {self.order_number} "
            f"{self.order_type} "
            f"{self.order_side} "
            f"{self.quantity:.8f}"
        )

        if self.limit_price is not None:
            info += f" @ ${round(self.limit_price, 2)}"

        return info
