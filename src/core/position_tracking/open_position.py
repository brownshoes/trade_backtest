from decimal import Decimal

from core.position_tracking.trade_data import TradeOverview, TradeResult
from core.order.order import Order

class OpenPosition:
    def __init__(self, trade_overview_buy: 'TradeOverview', trade_num) -> None:
        self.trade_num = trade_num
        self.trade_overview_buy: TradeOverview = trade_overview_buy
        self.entry_price = trade_overview_buy.executed_market_price
        self.entry_quantity = trade_overview_buy.quantity

        # Track how much of the position has been sold
        self.percent_sold = Decimal(0)
        self.quantity_sold = Decimal(0)
        self.times_sold = 0

        self.sell_trade_overviews = []
        self.trade_results = []

        # Prevent closing the same position multiple times
        self.is_locked = False
        self.placed_sell_order = None

        # Market tracking
        self.bars = 0
        self.max_price_seen = self.entry_price
        self.max_price_seen_timestamp = trade_overview_buy.executed_timestamp
        self.min_price_seen = self.entry_price
        self.min_price_seen_timestamp = trade_overview_buy.executed_timestamp

        self.run_up = Decimal(0)
        self.run_up_dollar = Decimal(0)
        self.run_up_pct = Decimal(0)

        self.drawdown = Decimal(0)
        self.drawdown_dollar = Decimal(0)
        self.drawdown_pct = Decimal(0)

    def update_position(self, exg_state) -> None:
        """Update run-up and drawdown stats based on current market price."""
        # Update max price
        if exg_state.current_price > self.max_price_seen:
            self.max_price_seen = exg_state.current_price
            self.max_price_seen_timestamp = exg_state.current_timestamp

        # Update min price
        if exg_state.current_price < self.min_price_seen:
            self.min_price_seen = exg_state.current_price
            self.min_price_seen_timestamp = exg_state.current_timestamp
        

        # self.run_up = self.max_price_seen - self.entry_price
        # self.run_up_pct = (self.run_up / self.entry_price) * Decimal(100)
        # self.run_up_dollar = self.run_up * self.entry_quantity


        # print(f"""
        # self.max_price_seen: {self.max_price_seen}
        # self.run_up: {self.run_up}
        # self.run_up_pct: {self.run_up_pct}
        # self.run_up_dollar: {self.run_up_dollar}
        # """)


        # self.drawdown = self.entry_price - self.min_price_seen
        # self.drawdown_pct = (self.drawdown / self.entry_price) * Decimal(100)
        # self.drawdown_dollar = self.drawdown * self.entry_quantity

        self.bars += 1  # Optionally increment bar count here

    def record_sell(self, sell_trade_overview: 'TradeOverview') -> None:
        """Record a completed or placed sell order."""
        quantity = sell_trade_overview.quantity
        self.quantity_sold += quantity
        self.percent_sold = self.quantity_sold / self.trade_overview_buy.quantity
        self.times_sold += 1

        trade_result = TradeResult(sell_trade_overview, self)
        sell_trade_overview.trade_result = trade_result
        self.sell_trade_overviews.append(sell_trade_overview)

        self.unlock()

        return trade_result

    def lock(self, sell_order: str) -> None:
        """Lock the position to prevent multiple simultaneous closes."""
        self.is_locked = True
        self.placed_sell_order = sell_order

    def unlock(self) -> None:
        """Unlock the position after the current sell order is processed."""
        self.is_locked = False
        self.placed_sell_order = None