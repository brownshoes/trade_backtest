from decimal import Decimal

from core.positions import OpenPosition, ClosedPosition, TradeOverview

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