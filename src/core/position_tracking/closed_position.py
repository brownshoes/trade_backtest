from decimal import Decimal
from datetime import datetime, timedelta

from core.position_tracking.open_position import OpenPosition
from core.position_tracking.trade_data import TradeOverview

class ClosedPosition:
    def __init__(self, open_position: 'OpenPosition'):
        self.open_position = open_position
        self.entry_trade = open_position.trade_overview_buy
        self.sell_trades = sorted(open_position.sell_trade_overviews, key=lambda t: t.executed_timestamp)

        # Combine all trades (entry + exits) chronologically
        self.all_trades = sorted([self.entry_trade] + self.sell_trades, key=lambda t: t.executed_timestamp)
        self.order_list = self.all_trades  # Alias for compatibility or clarity

        # Core stats
        self.quantity = sum(t.quantity for t in self.sell_trades)
        self.fees = self.calculate_fees(self.all_trades)
        self.open_market_price = self.entry_trade.executed_market_price
        self.close_market_price = self.sell_trades[-1].executed_market_price
        self.open_datetime = self.entry_trade.executed_datetime
        self.close_datetime = self.sell_trades[-1].executed_datetime
        self.open_timestamp = self.entry_trade.executed_timestamp
        self.close_timestamp = self.sell_trades[-1].executed_timestamp
        self.position_duration = self.calculate_duration()
        self.position_duration_formated = self.calculate_duration_formatted()

        # Profit/loss
        usd, percent = self.calculate_profit_and_loss()
        self.profit_and_loss = usd
        self.profit_and_loss_percent = percent

        # Run-up and drawdown
        self.run_up, self.run_up_pct = self.calculate_run_up()
        self.drawdown, self.drawdown_pct = self.calculate_drawdown()

        self.cumulative_profit_and_loss = None
    
    def calculate_fees(self, trades) -> Decimal:
        return sum((t.fee or Decimal(0)) for t in trades)

    def calculate_profit_and_loss(self) -> tuple[Decimal, Decimal]:
        entry_price = self.open_market_price
        entry_quantity = self.entry_trade.quantity

        # Entry value already has the fees removed
        #Ex: Buy .17507(entry_quantity) at $57057(entry_price). This costs $9998.92,
        # but we only get $9989 worth 
        total_entry_value = entry_price * entry_quantity 

        #Fees not included 
        total_exit_value = sum(t.executed_market_price * t.quantity for t in self.sell_trades)
        #net_pnl = total_exit_value - total_entry_value - self.fees

        #Fees. Only calculate the fess of the sells, The buy already has done so
        net_pnl = total_exit_value - total_entry_value - self.calculate_fees(self.sell_trades)
 
        pnl_pct = (net_pnl / total_entry_value) * Decimal(100) if total_entry_value != 0 else Decimal(0)
        return net_pnl, pnl_pct

    def calculate_duration(self) -> timedelta:
        return self.close_timestamp - self.open_timestamp
    
    def calculate_duration_formatted(self) -> str:
        # Convert float timestamps to datetime
        open_dt = datetime.fromtimestamp(self.open_timestamp)
        close_dt = datetime.fromtimestamp(self.close_timestamp)

        # Calculate duration
        duration: timedelta = close_dt - open_dt

        # Convert duration to HH:MM:SS
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def calculate_run_up(self) -> tuple[Decimal, Decimal]:
        entry_price = self.open_market_price

        if self.open_position.max_price_seen_timestamp == self.close_timestamp:
            max_price = self.close_market_price
        else:    
            max_price = self.open_position.max_price_seen

        run_up_dollar = (max_price - entry_price) * self.entry_trade.quantity
        run_up_pct = ((max_price - entry_price) / entry_price) * Decimal(100) if entry_price != 0 else Decimal(0)
        return run_up_dollar, run_up_pct

    def calculate_drawdown(self) -> tuple[Decimal, Decimal]:
        entry_price = self.open_market_price

        if self.open_position.min_price_seen_timestamp == self.close_timestamp:
            min_price = self.close_market_price
        else:    
            min_price = self.open_position.min_price_seen

        #result is always a negative value Flip: min_price - entry_price to be positive
        drawdown_dollar = (min_price - entry_price) * self.entry_trade.quantity
        drawdown_pct = ((min_price - entry_price) / entry_price) * Decimal(100) if entry_price != 0 else Decimal(0)
        
        return drawdown_dollar, drawdown_pct
    
    def __str__(self) -> str:
        GREEN = "\033[92m"
        RED = "\033[91m"
        YELLOW = "\033[93m"
        BLUE = "\033[94m"
        BOLD = "\033[1m"
        RESET = "\033[0m"

        def fmt_money(value):
            return f"${value:.2f}"

        def colorize(value, is_percent=False):
            color = GREEN if value >= 0 else RED
            symbol = "%" if is_percent else ""
            return f"{color}{value:.2f}{symbol}{RESET}"

        lines = [
            f"\n{BOLD}{BLUE}Closed Position Summary{RESET}",
            f"{BLUE}{'-'*40}{RESET}",
            f"{BOLD}Entry Time        :{RESET} {self.open_datetime}",
            f"{BOLD}Exit Time         :{RESET} {self.close_datetime}",
            f"{BOLD}Duration          :{RESET} {self.position_duration_formated}{RESET}",
            "",
            f"{BOLD}Entry Price       :{RESET} {GREEN}{fmt_money(self.open_market_price)}{RESET}",
            f"{BOLD}Exit Price        :{RESET} {GREEN}{fmt_money(self.close_market_price)}{RESET}",
            f"{BOLD}Quantity          :{RESET} {self.quantity:.6f}",
            "",
            f"{BOLD}Gross P&L         :{RESET} {colorize(self.profit_and_loss)}",
            f"{BOLD}P&L Percent       :{RESET} {colorize(self.profit_and_loss_percent, is_percent=True)}",
            f"{BOLD}Total Fees        :{RESET} {YELLOW}{fmt_money(self.fees)}{RESET}",
            "",
            f"{BOLD}Max Run-up        :{RESET} {GREEN}{fmt_money(self.run_up)} ({self.run_up_pct:.2f}%){RESET}",
            f"{BOLD}Max Drawdown      :{RESET} {RED}{fmt_money(self.drawdown)} ({self.drawdown_pct:.2f}%){RESET}",
            f"{BOLD}Cumulative P&L    :{RESET} {colorize(self.cumulative_profit_and_loss)}",
            f"{BLUE}{'-'*40}{RESET}",
        ]

        return "\n".join(lines)
    
    def to_dict(self):
        return {
            "quantity": self.quantity,
            "fees": round(float(self.fees), 2),
            "open_market_price": round(float(self.open_market_price), 2),
            "close_market_price": round(float(self.close_market_price), 2),
            "open_datetime": self.open_datetime,
            "close_datetime": self.close_datetime,
            "position_duration": self.position_duration,
            "position_duration_formatted": self.position_duration_formated,
            "profit_and_loss": round(float(self.profit_and_loss), 2),
            "profit_and_loss_percent": round(float(self.profit_and_loss_percent), 2),
            "run_up": round(float(self.run_up), 2),
            "run_up_pct": round(float(self.run_up_pct), 2),
            "drawdown": round(float(self.drawdown), 2),
            "drawdown_pct": round(float(self.drawdown_pct), 2),
            "cumulative_profit_and_loss": round(float(self.cumulative_profit_and_loss), 2),
            "trade_results": [
                sell_trade.trade_result.to_dict()
                for sell_trade in self.sell_trades
            ]
        }
