from decimal import Decimal
import math

from core.order.order import Order
from utils.calc import percent_of, quantize

import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)

'''Limit Buy. Buy amount of coin at a set percent below current price'''
class LimitBuyPercentEquity:
    def __init__(self, percent_equity=1.0, percent_below_current_price=0.01):
        self.percent_equity = Decimal(percent_equity)
        self.percent_below_current_price = Decimal(percent_below_current_price)

    def create_buy_order(self, identified_entries, trading_state, exg_state):
        limit_buy_price = Decimal(
            math.floor(
                exg_state.current_price - percent_of(self.percent_below_current_price, exg_state.current_price)
            )
        )
        logger.debug(f"exg_state.current_price: {exg_state.current_price}")
        logger.debug(f"limit_buy_price: {limit_buy_price}")

        dollar_amount = exg_state.USD_holdings * self.percent_equity
        fee_amount = dollar_amount * exg_state.maker_fee
        usd_after_fee = dollar_amount - fee_amount

        # Floor the USD available after subtracting fee
        usd_after_fee_floored = Decimal(math.floor(usd_after_fee))

        logger.debug(f"dollar_amount: {dollar_amount}")
        logger.debug(f"fee_amount: {fee_amount}")
        logger.debug(f"usd_after_fee (before floor): {usd_after_fee}")
        logger.debug(f"usd_after_fee_floored: {usd_after_fee_floored}")

        quantity = usd_after_fee_floored / limit_buy_price
        logger.debug(f"quantity before quantize: {quantity}")

        quantity = quantize(quantity)
        logger.debug(f"quantity after quantize: {quantity}")

        if exg_state.USD_holdings >= limit_buy_price * quantity:
            order_number = exg_state.provide_order_number()
            buy_order = Order(
                order_number,
                "LIMIT",
                "BUY",
                quantity,
                exg_state.maker_fee,
                exg_state.current_timestamp,
                limit_buy_price,
            )
            return buy_order
        else:
            logger.error(
                f"Not enough USD: ${exg_state.USD_holdings} Time: {exg_state.current_time}\n"
            )
            return None
