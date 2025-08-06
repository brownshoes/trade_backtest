from decimal import Decimal
from datetime import timedelta

from core.position_tracking.open_position import OpenPosition
from core.position_tracking.trade_data import TradeOverview

class ClosedPosition:
    def __init__(self, open_position: 'OpenPosition'):
        self.open_position = open_position
        self.entry_trade = open_position.buy_trade_overview
        self.sell_trades = sorted(open_position.sell_trade_overviews, key=lambda t: t.executed_datetime)

        # Combine all trades (entry + exits) chronologically
        self.all_trades = sorted([self.entry_trade] + self.sell_trades, key=lambda t: t.executed_datetime)
        self.order_list = self.all_trades  # Alias for compatibility or clarity

        # Core stats
        self.quantity = sum(t.quantity for t in self.sell_trades)
        self.fees = self.calculate_total_fees()
        self.open_market_price = self.entry_trade.executed_market_price
        self.close_market_price = self.sell_trades[-1].executed_market_price
        self.open_datetime = self.entry_trade.executed_datetime
        self.close_datetime = self.sell_trades[-1].executed_datetime
        self.position_duration = self.calculate_duration()

        # Profit/loss
        usd, percent = self.calculate_profit_and_loss()
        self.profit_and_loss = usd
        self.profit_and_loss_percent = percent

        # Run-up and drawdown
        self.run_up, self.run_up_pct = self.calculate_run_up()
        self.drawdown, self.drawdown_pct = self.calculate_drawdown()

    def calculate_total_fees(self) -> Decimal:
        return sum((t.fee or Decimal(0)) for t in self.all_trades)

    def calculate_profit_and_loss(self) -> tuple[Decimal, Decimal]:
        entry_price = self.open_market_price
        entry_quantity = self.entry_trade.quantity
        total_entry_value = entry_price * entry_quantity

        total_exit_value = sum(t.executed_market_price * t.quantity for t in self.sell_trades)
        net_pnl = total_exit_value - total_entry_value - self.fees

        pnl_pct = (net_pnl / total_entry_value) * Decimal(100) if total_entry_value != 0 else Decimal(0)
        return net_pnl, pnl_pct

    def calculate_duration(self) -> timedelta:
        return self.close_datetime - self.open_datetime

    def calculate_run_up(self) -> tuple[Decimal, Decimal]:
        entry_price = self.open_market_price
        max_price = self.open_position.max_price_seen
        run_up_dollar = (max_price - entry_price) * self.entry_trade.quantity
        run_up_pct = ((max_price - entry_price) / entry_price) * Decimal(100) if entry_price != 0 else Decimal(0)
        return run_up_dollar, run_up_pct

    def calculate_drawdown(self) -> tuple[Decimal, Decimal]:
        entry_price = self.open_market_price
        min_price = self.open_position.min_price_seen
        drawdown_dollar = (entry_price - min_price) * self.entry_trade.quantity
        drawdown_pct = ((entry_price - min_price) / entry_price) * Decimal(100) if entry_price != 0 else Decimal(0)
        return drawdown_dollar, drawdown_pct
    
    def summary(self) -> str:
        return (
            f"📊 Closed Position Summary\n"
            f"{'-'*40}\n"
            f"📅 Entry Time       : {self.open_datetime}\n"
            f"📅 Exit Time        : {self.close_datetime}\n"
            f"⏳ Duration         : {self.position_duration}\n\n"
            f"💰 Entry Price      : {self.open_market_price:.2f}\n"
            f"💰 Exit Price       : {self.close_market_price:.2f}\n"
            f"🔢 Quantity         : {self.quantity:.6f}\n\n"
            f"💵 Gross P&L        : ${self.profit_and_loss:.2f}\n"
            f"📈 P&L Percent      : {self.profit_and_loss_percent:.2f}%\n"
            f"💸 Total Fees       : ${self.fees:.2f}\n\n"
            f"📈 Max Run-up       : ${self.run_up:.2f} ({self.run_up_pct:.2f}%)\n"
            f"📉 Max Drawdown     : ${self.drawdown:.2f} ({self.drawdown_pct:.2f}%)\n"
            f"{'-'*40}"
        )