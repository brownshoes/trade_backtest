from factories.config import Config
from factories.test_classes import Car, Person
from core.time_series import TimeSeries

config = Config(
    mode="BACKTEST",
    start_time="2024-01-01 00:00",
    end_time="2024-10-01 00:00",
    USD_holdings=10000.0,
    coin_holdings=1.5,
    maker_fee=0.001,
    taker_fee=0.002,
    time_series=['15m', '1h'],
    csv_input_file="csv\\csv_backtest\\short_btc.csv"
)
