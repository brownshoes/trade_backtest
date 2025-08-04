from decimal import Decimal
import datetime
from datetime import timedelta

import math
from statistics import mean, stdev

from core.trading_state import TradingState

from order.order import Order

from utils.calc import percent_change, what_percent_is

class OpenPosition:
    def __init__(self, buy_trade_overview: 'TradeOverview', trade_num) -> None:
        self.trade_num = trade_num
        self.buy_trade_overview: TradeOverview = buy_trade_overview
        self.entry_price = buy_trade_overview.executed_market_price
        self.entry_quantity = buy_trade_overview.quantity

        # Track how much of the position has been sold
        self.percent_sold = Decimal(0)
        self.amount_sold = Decimal(0)
        self.times_sold = 0

        self.completed_sell_orders = []

        # Prevent closing the same position multiple times
        self.is_locked = False
        self.placed_sell_order = None

        # Market tracking
        self.bars = 0
        self.max_price_seen = self.entry_price
        self.min_price_seen = self.entry_price

        self.run_up = Decimal(0)
        self.run_up_dollar = Decimal(0)
        self.run_up_pct = Decimal(0)

        self.drawdown = Decimal(0)
        self.drawdown_dollar = Decimal(0)
        self.drawdown_pct = Decimal(0)

    def update_position(self, current_price: Decimal) -> None:
        """Update run-up and drawdown stats based on current market price."""
        self.max_price_seen = max(self.max_price_seen, current_price)
        self.min_price_seen = min(self.min_price_seen, current_price)

        self.run_up = self.max_price_seen - self.entry_price
        self.run_up_pct = (self.run_up / self.entry_price) * Decimal(100)
        self.run_up_dollar = self.run_up * self.entry_quantity

        self.drawdown = self.entry_price - self.min_price_seen
        self.drawdown_pct = (self.drawdown / self.entry_price) * Decimal(100)
        self.drawdown_dollar = self.drawdown * self.entry_quantity

        self.bars += 1  # Optionally increment bar count here

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


class TradeOverview:
    def __init__(self, order):
        self.order = order
        self.order_number = order.order_string()

        # Placed data
        self.placed_datetime = order.placed.datetime
        self.placed_market_price = order.placed.market_price

        # Executed data
        self.executed_datetime = order.execution.datetime
        self.executed_market_price = order.execution.market_price
        self.dollar_amount = order.execution.dollar_amount
        self.quantity = order.execution.quantity
        self.fee = order.fee
        self.time_to_execute = order.execution.time_to_execute
        self.slippage = order.execution.price_difference
        self.slippage_pct = order.execution.price_difference_percent

    def __str__(self):
        return (
            f"\n {self.order.order_side} EXECUTED -> {self.order_number}"
            f"\n\t Placed Time: {self.placed_datetime}"
            f"\n\t Placed Price: ${self.placed_market_price:.2f}"
            f"\n Executed: ->"
            f"\n\t Time: {self.executed_datetime}"
            f"\n\t Market Price: ${self.executed_market_price:.2f}"
            f"\n\t USD: ${self.dollar_amount:.2f}"
            f"\n\t Coin: {self.coin_amount:.8f}"
            f"\n\t Fee: {self.fee:.8f}"
            f"\n\t Time To Execute: {self.time_to_execute:.2f} sec"
            f"\n\t Slippage: ${self.slippage:.2f} ({self.slippage_pct:.2f}%)"
        )

class TradeResults:
    def __init__(self, sell_trade_overview: 'TradeOverview', open_position: 'OpenPosition'):
        self.sell_trade_overview = sell_trade_overview

        # Core data
        self.entry_price = open_position.entry_price
        self.exit_price = sell_trade_overview.executed_market_price
        self.quantity = sell_trade_overview.quantity
        self.fee = sell_trade_overview.fee

        # Total % of the original position this sell represents
        self.percent_of_position = (self.quantity / open_position.entry_quantity) * Decimal(100)
        self.total_position_percent_sold = open_position.percent_sold * Decimal(100)

        # Run-up & drawdown before the sell
        run_up = open_position.max_price_seen - self.entry_price
        self.run_up_dollar = run_up * self.quantity
        self.run_up_pct = (run_up / self.entry_price) * Decimal(100) if self.entry_price != 0 else Decimal(0)

        drawdown = self.entry_price - open_position.min_price_seen
        self.drawdown_dollar = drawdown * self.quantity
        self.drawdown_pct = (drawdown / self.entry_price) * Decimal(100) if self.entry_price != 0 else Decimal(0)

        # Profit/Loss for this sell
        pnl = (self.exit_price - self.entry_price) * self.quantity
        self.profit_and_loss = pnl - self.fee
        self.profit_and_loss_pct = (self.profit_and_loss / (self.entry_price * self.quantity)) * Decimal(100) \
            if self.entry_price != 0 else Decimal(0)


class ClosedPosition:
    def __init__(self, open_position: 'OpenPosition', sell_trade_overviews: list['TradeOverview']):
        self.open_position = open_position
        self.entry_trade = open_position.buy_trade_overview
        self.sell_trades = sorted(sell_trade_overviews, key=lambda t: t.executed_datetime)

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


class Statistics:
    def __init__(self, trading_state: 'TradingState', candle_size: timedelta, risk_free_rate: float = 0.0):
        self.trading_state = trading_state
        self.candle_size = candle_size

        self.risk_free_rate = Decimal(risk_free_rate)

        self._compute()


    def _compute(self):
        closed = self.trading_state.closed_positions
        equity_log = self.trading_state.equity_log

        self.total_trades = len(closed)
        self.total_open_trades = len(self.trading_state.open_positions)
        self.total_fees = sum(pos.fees for pos in closed)

        if self.total_trades == 0:
            self._set_defaults()
            return

        self.total_profit_and_loss = self.trading_state.cumulative_pnl
        self.total_profit_and_loss_percent = sum(pos.profit_and_loss_percent for pos in closed)

        self.max_equity_drawdown = self.trading_state.max_drawdown
        self.max_equity_drawdown_percent = self.trading_state.max_drawdown_percent

        # Win/loss splits
        winning = [pos for pos in closed if pos.profit_and_loss > 0]
        losing = [pos for pos in closed if pos.profit_and_loss < 0]

        self.winning_trades = len(winning)
        self.losing_trades = len(losing)
        self.percent_profitable = (self.winning_trades / self.total_trades) * 100

        # Averages
        self.avg_profit_and_loss = self.total_profit_and_loss / self.total_trades
        self.avg_profit_and_loss_percent = self.total_profit_and_loss_percent / self.total_trades

        self.avg_winning_trade = (sum(p.profit_and_loss for p in winning) / self.winning_trades) if self.winning_trades else Decimal(0)
        self.avg_winning_trade_percent = (sum(p.profit_and_loss_percent for p in winning) / self.winning_trades) if self.winning_trades else Decimal(0)

        self.avg_losing_trade = (sum(p.profit_and_loss for p in losing) / self.losing_trades) if self.losing_trades else Decimal(0)
        self.avg_losing_trade_percent = (sum(p.profit_and_loss_percent for p in losing) / self.losing_trades) if self.losing_trades else Decimal(0)

        self.ratio_avg_win_to_loss = (
            abs(self.avg_winning_trade / self.avg_losing_trade)
            if self.avg_losing_trade != 0 else Decimal('Infinity')
        )

        self.largest_winning_trade = max((p.profit_and_loss for p in winning), default=Decimal(0))
        self.largest_winning_trade_percent = max((p.profit_and_loss_percent for p in winning), default=Decimal(0))

        self.largest_losing_trade = min((p.profit_and_loss for p in losing), default=Decimal(0))
        self.largest_losing_trade_percent = min((p.profit_and_loss_percent for p in losing), default=Decimal(0))

        # Bars and durations
        self.avg_num_bars_in_trades = self._avg_bars(closed)
        self.avg_num_bars_in_winning_trades = self._avg_bars(winning)
        self.avg_num_bars_in_losing_trades = self._avg_bars(losing)

        self.sharpe_ratio = self._calculate_sharpe_ratio()
        self.sortino_ratio = self._calculate_sortino_ratio()

        # Trade-by-trade log (overview)
        self.overview = self.trading_state.equity_log

    def _avg_bars(self, trades):
        if not trades:
            return 0
        total_seconds = sum(p.position_duration.total_seconds() for p in trades)
        avg_duration = total_seconds / len(trades)
        return avg_duration / self.candle_size.total_seconds()
    

    def _calculate_sharpe_ratio(self):
        returns = []

        equity_log = self.trading_state.equity_log
        if len(equity_log) < 2:
            return None  # Not enough data

        # Compute returns as percent change in cumulative P&L
        for i in range(1, len(equity_log)):
            prev = equity_log[i - 1]['cumulative_pnl']
            curr = equity_log[i]['cumulative_pnl']
            if prev == 0:
                continue  # Avoid divide by zero
            ret = (curr - prev) / prev
            returns.append(ret)

        if len(returns) < 2:
            return None

        avg_return = mean(returns)
        stddev = stdev(returns)

        if stddev == 0:
            return Decimal('Infinity') if avg_return > 0 else Decimal(0)

        # Assume 0 risk-free rate unless specified
        excess_return = avg_return - float(self.risk_free_rate)

        sharpe = excess_return / stddev
        return round(Decimal(sharpe), 4)
    
    def _calculate_sortino_ratio(self):
        equity_log = self.trading_state.equity_log
        if len(equity_log) < 2:
            return None

        returns = []
        for i in range(1, len(equity_log)):
            prev = equity_log[i - 1]['cumulative_pnl']
            curr = equity_log[i]['cumulative_pnl']
            if prev == 0:
                continue
            ret = (curr - prev) / prev
            returns.append(ret)

        if len(returns) < 2:
            return None

        avg_return = mean(returns)
        downside_returns = [r for r in returns if r < 0]

        if not downside_returns:
            return Decimal('Infinity') if avg_return > 0 else Decimal(0)

        downside_deviation = stdev(downside_returns)

        if downside_deviation == 0:
            return Decimal('Infinity') if avg_return > 0 else Decimal(0)

        excess_return = avg_return - float(self.risk_free_rate)
        sortino = excess_return / downside_deviation

        return round(Decimal(sortino), 4)

    def _set_defaults(self):
        # Net total profit/loss (USD)
        self.total_profit_and_loss = Decimal(0)
        
        # Net total profit/loss in percentage terms
        self.total_profit_and_loss_percent = Decimal(0)
        
        # Maximum equity drawdown in absolute dollars
        self.max_equity_drawdown = Decimal(0)
        
        # Maximum drawdown as a percent from peak equity
        self.max_equity_drawdown_percent = Decimal(0)
        
        # Total fees incurred across all closed trades
        self.total_fees = Decimal(0)
        
        # Number of closed trades
        self.total_trades = 0
        
        # Number of currently open positions
        self.total_open_trades = len(self.trading_state.open_positions)
        
        # Number of trades with positive profit
        self.winning_trades = 0
        
        # Number of trades with negative profit
        self.losing_trades = 0
        
        # Percentage of trades that are profitable
        self.percent_profitable = 0
        
        # Average profit/loss per trade (USD)
        self.avg_profit_and_loss = Decimal(0)
        
        # Average profit/loss per trade (%)
        self.avg_profit_and_loss_percent = Decimal(0)
        
        # Average profit from winning trades (USD)
        self.avg_winning_trade = Decimal(0)
        
        # Average profit from winning trades (%)
        self.avg_winning_trade_percent = Decimal(0)
        
        # Average loss from losing trades (USD)
        self.avg_losing_trade = Decimal(0)
        
        # Average loss from losing trades (%)
        self.avg_losing_trade_percent = Decimal(0)
        
        # Risk/reward ratio: average win / average loss
        self.ratio_avg_win_to_loss = Decimal(0)
        
        # Largest single trade profit (USD)
        self.largest_winning_trade = Decimal(0)
        
        # Largest single trade profit (%)
        self.largest_winning_trade_percent = Decimal(0)
        
        # Largest single trade loss (USD)
        self.largest_losing_trade = Decimal(0)
        
        # Largest single trade loss (%)
        self.largest_losing_trade_percent = Decimal(0)
        
        # Average number of bars held for all trades
        self.avg_num_bars_in_trades = 0
        
        # Average number of bars held for winning trades
        self.avg_num_bars_in_winning_trades = 0
        
        # Average number of bars held for losing trades
        self.avg_num_bars_in_losing_trades = 0

        # Overview of each trade for equity tracking (used for plotting or data export)
        self.overview = []

        # Risk-adjusted return metrics
        self.sharpe_ratio = None       # Measures return per unit of total volatility
        self.sortino_ratio = None      # Measures return per unit of downside volatility only

    def summary_string_color(self) -> str:
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
            f"{BOLD}{BLUE}🔎 Strategy Performance Summary{RESET}",
            f"{BLUE}{'-' * 45}{RESET}",
            f"{BOLD}Total Trades Closed     :{RESET} {self.total_trades}",
            f"{BOLD}Open Positions          :{RESET} {self.total_open_trades}",
            f"{BOLD}Profitable Trades       :{RESET} {GREEN if self.percent_profitable >= 50 else YELLOW}{self.winning_trades} ({self.percent_profitable:.2f}%){RESET}",
            f"{BOLD}Losing Trades           :{RESET} {self.losing_trades}",
            "",
            f"{BOLD}Total P&L               :{RESET} {colorize(self.total_profit_and_loss)}",
            f"{BOLD}Total P&L (%)           :{RESET} {colorize(self.total_profit_and_loss_percent, is_percent=True)}",
            f"{BOLD}Total Fees Paid         :{RESET} {YELLOW}{fmt_money(self.total_fees)}{RESET}",
            "",
            f"{BOLD}Avg Trade P&L           :{RESET} {colorize(self.avg_profit_and_loss)} ({colorize(self.avg_profit_and_loss_percent, True)})",
            f"{BOLD}Avg Winning Trade       :{RESET} {GREEN}{fmt_money(self.avg_winning_trade)} ({self.avg_winning_trade_percent:.2f}%){RESET}",
            f"{BOLD}Avg Losing Trade        :{RESET} {RED}{fmt_money(self.avg_losing_trade)} ({self.avg_losing_trade_percent:.2f}%){RESET}",
            f"{BOLD}Win/Loss Ratio          :{RESET} {self.ratio_avg_win_to_loss:.2f}",
            "",
            f"{BOLD}Largest Win             :{RESET} {GREEN}{fmt_money(self.largest_winning_trade)} ({self.largest_winning_trade_percent:.2f}%){RESET}",
            f"{BOLD}Largest Loss            :{RESET} {RED}{fmt_money(self.largest_losing_trade)} ({self.largest_losing_trade_percent:.2f}%){RESET}",
            "",
            f"{BOLD}Max Drawdown            :{RESET} {YELLOW}{fmt_money(self.max_equity_drawdown)} ({self.max_equity_drawdown_percent:.2f}%){RESET}",
            f"{BOLD}Sharpe Ratio            :{RESET} {self.sharpe_ratio if self.sharpe_ratio is not None else 'N/A'}",
            f"{BOLD}Sortino Ratio           :{RESET} {self.sortino_ratio if self.sortino_ratio is not None else 'N/A'}",
            "",
            f"{BOLD}Avg Bars in Trades      :{RESET} {self.avg_num_bars_in_trades:.1f}",
            f"{BOLD}Avg Bars (Winners)      :{RESET} {self.avg_num_bars_in_winning_trades:.1f}",
            f"{BOLD}Avg Bars (Losers)       :{RESET} {self.avg_num_bars_in_losing_trades:.1f}",
            f"{BLUE}{'-' * 45}{RESET}",
        ]

        return "\n".join(lines)


    def summary_string(self) -> str:
        lines = [
            "🔎 Strategy Performance Summary",
            "----------------------------------------",
            f"Total Trades Closed     : {self.total_trades}",
            f"Open Positions          : {self.total_open_trades}",
            f"Profitable Trades       : {self.winning_trades} ({self.percent_profitable:.2f}%)",
            f"Losing Trades           : {self.losing_trades}",
            "",
            f"Total P&L               : ${self.total_profit_and_loss:.2f}",
            f"Total P&L (%)           : {self.total_profit_and_loss_percent:.2f}%",
            f"Total Fees Paid         : ${self.total_fees:.2f}",
            "",
            f"Avg Trade P&L           : ${self.avg_profit_and_loss:.2f} ({self.avg_profit_and_loss_percent:.2f}%)",
            f"Avg Winning Trade       : ${self.avg_winning_trade:.2f} ({self.avg_winning_trade_percent:.2f}%)",
            f"Avg Losing Trade        : ${self.avg_losing_trade:.2f} ({self.avg_losing_trade_percent:.2f}%)",
            f"Win/Loss Ratio          : {self.ratio_avg_win_to_loss:.2f}",
            "",
            f"Largest Win             : ${self.largest_winning_trade:.2f} ({self.largest_winning_trade_percent:.2f}%)",
            f"Largest Loss            : ${self.largest_losing_trade:.2f} ({self.largest_losing_trade_percent:.2f}%)",
            "",
            f"Max Drawdown            : ${self.max_equity_drawdown:.2f} ({self.max_equity_drawdown_percent:.2f}%)",
            f"Sharpe Ratio            : {self.sharpe_ratio if self.sharpe_ratio is not None else 'N/A'}",
            f"Sortino Ratio           : {self.sortino_ratio if self.sortino_ratio is not None else 'N/A'}",
            "",
            f"Avg Bars in Trades      : {self.avg_num_bars_in_trades:.1f}",
            f"Avg Bars (Winners)      : {self.avg_num_bars_in_winning_trades:.1f}",
            f"Avg Bars (Losers)       : {self.avg_num_bars_in_losing_trades:.1f}",
            "----------------------------------------"
        ]
        return "\n".join(lines)
