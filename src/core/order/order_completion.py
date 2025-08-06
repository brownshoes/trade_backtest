from abc import ABC, abstractmethod
from decimal import Decimal

from core.order.order_classes import OrderExecution

class OrderCompletion(ABC):
    @abstractmethod
    def complete_order(self, order, exg_state):
        """Complete the order execution and update state."""
        pass

def order_completion_factory(order_completion_name: str) -> OrderCompletion:
    completions = {
        "BACKTEST": BacktestCompletion,
        # add more as needed
    }
    completion_class = completions.get(order_completion_name.upper())
    if not completion_class:
        raise ValueError(f"No order completion handler found for: {order_completion_name}")
    return completion_class()


class BacktestCompletion(OrderCompletion):
    def complete_order(self, order, exg_state):
        current_price = exg_state.current_price

        #revert back to original funds
        order.restore_funds(exg_state)

        #Calculate fee for market and stop orders
        fee = order.quantity * current_price * order.fee_percentage

        '''If this is a limit buy, then we want to execute on the limit price, not the current market price'''
        execution_price = (
            order.limit_price if order.order_type == "LIMIT" else current_price
        )

        if order.order_side == "BUY":
            USD_change = 0 - (order.quantity * execution_price + fee)
            coin_change = order.quantity

        elif order.order_side == "SELL":
            USD_change = (order.quantity * execution_price) - fee
            coin_change = 0 - order.quantity

        # Update holdings on the state object
        exg_state.update_USD_holdings(USD_change)
        exg_state.update_coin_holdings(coin_change)

        # Record execution details using OrderExecution object
        execution_timestamp = exg_state.current_timestamp

        order.set_order_execution(
            timestamp = execution_timestamp,
            datetime = exg_state.get_current_datetime(),
            market_price = execution_price,
            dollar_amount = abs(USD_change),
            coin_amount = abs(coin_change),
            fee = fee,
            time_to_execute = execution_timestamp - order.creation_timestamp,
            price_difference = Decimal('0'),  # Could calculate based on initial price if needed
            price_difference_percent = Decimal('0'),
        )


class GeminiExecutor(OrderCompletion):
    def complete_order(self, order, exg_state):
        pass

