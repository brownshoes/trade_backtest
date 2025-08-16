from decimal import Decimal


class TradeOverview:
    def __init__(self, order):
        self.order = order
        self.order_number = order.order_number

        # Placed data
        self.placed_datetime = order.placed.datetime
        self.placed_market_price = order.placed.market_price

        # Executed data
        self.executed_timestamp = order.execution.timestamp
        self.executed_datetime = order.execution.datetime
        self.executed_market_price = order.execution.market_price
        self.dollar_amount = order.execution.dollar_amount
        self.quantity = order.execution.quantity
        self.fee = order.execution.fee
        self.time_to_execute = order.execution.time_to_execute
        self.slippage = order.execution.price_difference
        self.slippage_pct = order.execution.price_difference_percent

        self.trade_result = None

    def __str__(self):
        return (
            f"\n {self.order.order_side} EXECUTED -> {self.order.order_string()}"
            f"\n\t Placed Time: {self.placed_datetime}"
            f"\n\t Placed Price: ${self.placed_market_price:.2f}"
            f"\n Executed: ->"
            f"\n\t Time: {self.executed_datetime}"
            f"\n\t Market Price: ${self.executed_market_price:.2f}"
            f"\n\t USD: ${self.dollar_amount:.2f}"
            f"\n\t Quantity: {self.quantity:.8f}"
            f"\n\t Fee: {self.fee:.8f}"
            f"\n\t Time To Execute: {self.time_to_execute:.2f} sec"
            f"\n\t Slippage: ${self.slippage:.2f} ({self.slippage_pct:.2f}%)"
        )

class TradeResult:
    def __init__(self, sell_trade_overview: 'TradeOverview', open_position):
        # Core data
        self.entry_price = open_position.entry_price
        self.exit_price = sell_trade_overview.executed_market_price
        self.quantity = sell_trade_overview.quantity
        self.fee = sell_trade_overview.fee
        self.entry_datetime = open_position.trade_overview_buy.executed_datetime
        self.exit_datetime = sell_trade_overview.executed_datetime

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
            f"\n{BOLD}{BLUE}🔽 Trade Result Summary{RESET}",
            f"{BLUE}{'-' * 45}{RESET}",
            f"{BOLD}Entry Price             :{RESET} {fmt_money(self.entry_price)}",
            f"{BOLD}Exit Price              :{RESET} {fmt_money(self.exit_price)}",
            f"{BOLD}Quantity Sold           :{RESET} {self.quantity:.4f}",
            f"{BOLD}Fee Paid                :{RESET} {YELLOW}{fmt_money(self.fee)}{RESET}",
            f"{BOLD}% of Position Sold      :{RESET} {self.percent_of_position:.2f}%",
            f"{BOLD}Total % Sold So Far     :{RESET} {self.total_position_percent_sold:.2f}%",
            "",
            f"{BOLD}Run-up (Value)          :{RESET} {fmt_money(self.run_up_dollar)}",
            f"{BOLD}Run-up (Percent)        :{RESET} {colorize(self.run_up_pct, is_percent=True)}",
            f"{BOLD}Drawdown (Value)        :{RESET} {fmt_money(self.drawdown_dollar)}",
            f"{BOLD}Drawdown (Percent)      :{RESET} {colorize(self.drawdown_pct, is_percent=True)}",
            "",
            f"{BOLD}Profit / Loss           :{RESET} {colorize(self.profit_and_loss)}",
            f"{BOLD}Profit / Loss (%)       :{RESET} {colorize(self.profit_and_loss_pct, is_percent=True)}",
            f"{BLUE}{'-' * 45}{RESET}",
        ]

        return "\n".join(lines)
