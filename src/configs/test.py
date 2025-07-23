from factories.config import Config
from factories.test_classes import Car, Person
from core.time_series import TimeSeries

ts1 = TimeSeries(candle_size = "15m")

config = Config(
    mode = "backtest",
    start_time = "2024-06-13 00:00",
    end_time = "2024-06-15 12:00",
    vehicles={
        "my_car": Car("Toyota", "Corolla", 2020)
        },
    people={},
    time_series=[ts1],
    csv_input_file="csv\\csv_backtest\\short_btc.csv"
)
