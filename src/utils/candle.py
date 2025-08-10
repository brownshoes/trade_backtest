from collections import namedtuple

from utils.time_conversion import timestamp_to_datetime

candle_columns = ["Datetime", "Timestamp", "Open", "High", "Low", "Close", "Volume"]

Candle = namedtuple("Candle", candle_columns)

def create_empty_candle(timestamp):
    return Candle(
        Datetime=timestamp_to_datetime(timestamp),
        Timestamp=timestamp,
        Open=0,
        High=0,
        Low=0,
        Close=0,
        Volume=0
    )