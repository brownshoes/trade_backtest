from decimal import Decimal

from order.order import Order

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
        self.sell_order = None

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
        self.sell_order = sell_order

    def unlock(self) -> None:
        """Unlock the position after the current sell order is processed."""
        self.is_locked = False
        self.sell_order = None

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