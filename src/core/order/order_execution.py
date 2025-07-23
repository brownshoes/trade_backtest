from decimal import Decimal

class OrderExecution:
    def __init__(
        self,
        execution_time: str,
        execution_market_price: Decimal,
        execution_dollar_amount: Decimal,
        execution_coin_amount: Decimal,
        fee: Decimal,
        time_to_execute: float,  # e.g., seconds
        execution_price_difference: Decimal,
        execution_price_difference_percent: Decimal,
    ):
        self.execution_time = execution_time
        self.execution_market_price = execution_market_price
        self.execution_dollar_amount = execution_dollar_amount
        self.execution_coin_amount = execution_coin_amount
        self.fee = fee
        self.time_to_execute = time_to_execute
        self.execution_price_difference = execution_price_difference
        self.execution_price_difference_percent = execution_price_difference_percent