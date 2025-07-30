from decimal import Decimal
import datetime

from order.order import Order

from utils.calc import percent_change

class OpenPosition:
    def __init__(self, buy_order: 'Order') -> None:
        self.buy_order: Order = buy_order

        # Track how much of the position has been sold
        self.percent_sold = Decimal(0)
        self.amount_sold = Decimal(0)
        self.times_sold = 0

        self.completed_sell_orders = []

        # Prevent closing the same position multiple times
        self.is_locked = False
        self.placed_sell_order = None

    def record_sell(self, sell_order: 'Order') -> None:
        """Record a completed or placed sell order."""
        executed_amount = sell_order.execution.coin_amount
        self.amount_sold += executed_amount
        self.percent_sold = self.amount_sold / self.buy_order.execution.coin_amount
        self.times_sold += 1

        self.completed_sell_orders.append(sell_order)

        self.unlock()

    def lock(self, sell_order: str) -> None:
        """Lock the position to prevent multiple simultaneous closes."""
        self.is_locked = True
        self.placed_sell_order = sell_order

    def unlock(self) -> None:
        """Unlock the position after the current sell order is processed."""
        self.is_locked = False
        self.placed_sell_order = None

    def is_fully_sold(self) -> bool:
        """Return whether the position has been entirely sold."""
        return self.amount_sold >= self.buy_order.execution_coin_amount

    def remaining_amount(self) -> Decimal:
        """Return the remaining unsold coin amount."""
        return self.buy_order.execution_coin_amount - self.amount_sold

    def usd_value_remaining(self, current_price: Decimal) -> Decimal:
        """Return USD value of remaining unsold coins at current price."""
        return self.remaining_amount() * current_price

    def summary(self) -> str:
        """Human-readable status of the position."""
        return (
            f"Buy Order: {self.buy_order.order_string()} | "
            f"Sold: {self.amount_sold:.6f} ({self.percent_sold:.2%}) | "
            f"Remaining: {self.remaining_amount():.6f} | "
            f"Sells: {len(self.completed_sell_orders)}"
        )
    
class ClosedPosition:
    def __init__(self, open_position):
        self.position = open_position
        self.buy_order = self.position.buy_order
        self.last_sell_order = self.position.completed_sell_orders[-1]

        self.position_open_time = self.buy_order.execution.datetime
        self.position_close_time = self.last_sell_order.execution.datetime
        self.position_duration = datetime.timedelta(
            seconds=self.last_sell_order.execution.timestamp - self.buy_order.execution.timestamp
        )

        self.market_at_open = self.buy_order.execution.market_price
        self.market_at_close = self.last_sell_order.execution.market_price
        self.market_percent_change = percent_change(self.market_at_close, self.market_at_open)

        # Dollar amount to open the position (includes buy fee)
        self.open_position_dollar_amount = self.buy_order.execution.dollar_amount + self.buy_order.execution.fee

        # Dollar value of all executed sell orders (excluding fees)
        self.close_dollar_amount = self._get_close_dollar_amount()

        # Net USD profit/loss
        self.dollar_outcome = self.close_dollar_amount - self.open_position_dollar_amount

        # Percent profit/loss
        self.percent_result = percent_change(self.close_dollar_amount, self.open_position_dollar_amount)

        self.total_fees = self._total_fees()

    def _get_close_dollar_amount(self):
        return sum((order.execution.dollar_amount for order in self.position.completed_sell_orders), Decimal(0))

    def _total_fees(self):
        return self.buy_order.execution.fee + sum(
            (order.execution.fee for order in self.position.completed_sell_orders),
            Decimal(0)
        )

    def closed_position_results_string(self):
        return (
            "\n Position Results"
            f"\n\tDuration: {self.position_duration}  Open({self.position_open_time}) -> Close({self.position_close_time})"
            f"\n\tMarket at Open: ${self.market_at_open:.2f}  Market at Close: ${self.market_at_close:.2f}  % Change: {self.market_percent_change:.2f}"
            f"\n\tPosition Open: ${self.open_position_dollar_amount:.2f}  Position Close: ${self.close_dollar_amount:.2f}"
            f"\n\tOutcome: ${self.dollar_outcome:.2f}  % Outcome: {self.percent_result:.2f}  Fees: ${self.total_fees:.2f}"
        )
