from decimal import Decimal

class OrderPlaced:
    def __init__(
        self,
        timestamp: float,
        datetime: str,
        market_price: Decimal
    ):
        self.timestamp = timestamp
        self.datetime = datetime
        self.market_price = market_price

class OrderExecution:
    def __init__(
        self,
        timestamp: float,
        datetime: str,
        market_price: Decimal,
        dollar_amount: Decimal,
        quantity: Decimal,
        fee: Decimal,
        time_to_execute: float,  # e.g., seconds
        price_difference: Decimal,
        price_difference_percent: Decimal,
    ):
        self.timestamp = timestamp
        self.datetime = datetime
        self.market_price = market_price
        self.dollar_amount = dollar_amount
        self.quantity = quantity
        self.fee = fee
        self.time_to_execute = time_to_execute
        self.price_difference = price_difference #Slipage
        self.price_difference_percent = price_difference_percent