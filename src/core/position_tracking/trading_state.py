from decimal import Decimal

from core.position_tracking.closed_position import ClosedPosition
from core.position_tracking.open_position import OpenPosition
from core.position_tracking.trade_data import TradeOverview


class TradingState:
    def __init__(self):
        self.open_positions: dict[str, OpenPosition] = {}
        self.closed_positions: list[ClosedPosition] = []

        self.open_buy_orders: dict[str, TradeOverview] = {}
        self.open_sell_orders: dict[str, TradeOverview] = {}

        self.cumulative_pnl = Decimal(0)
        self.max_equity = Decimal(0)
        self.max_drawdown = Decimal(0)
        self.max_drawdown_percent = Decimal(0)

        self.equity_log: list[dict] = []

    def get_position_by_sell_order_number(self, order_number: str) -> 'OpenPosition | None':
        for position in self.open_positions.values():
            if position.placed_sell_order is not None:
                if position.placed_sell_order.order_number == order_number:
                    return position
        return None

    def add_closed_position(self, closed_position: 'ClosedPosition'):
        self.closed_positions.append(closed_position)

        pnl = closed_position.profit_and_loss
        self.cumulative_pnl += pnl

        # Update max equity
        if self.cumulative_pnl > self.max_equity:
            self.max_equity = self.cumulative_pnl

        # Calculate drawdown from peak
        drawdown = self.max_equity - self.cumulative_pnl
        drawdown_pct = (
            (drawdown / self.max_equity) * Decimal(100)
            if self.max_equity > 0 else Decimal(0)
        )

        # Update max drawdown if worse
        self.max_drawdown = max(self.max_drawdown, drawdown)
        self.max_drawdown_percent = max(self.max_drawdown_percent, drawdown_pct)

        # Record snapshot
        self.equity_log.append({
            "trade_num": len(self.closed_positions),
            "timestamp": closed_position.close_datetime,
            "pnl": pnl,
            "cumulative_pnl": self.cumulative_pnl,
            "max_drawdown": self.max_drawdown,
            "max_drawdown_percent": self.max_drawdown_percent
        })