from collections import namedtuple

from utils.time_conversion import timestamp_to_string

Candle = namedtuple("Candle", ["Datetime", "Timestamp", "Open", "High", "Low", "Close", "Volume"])

def create_empty_candle(timestamp):
    return Candle(
        Datetime=timestamp_to_string(timestamp),
        Timestamp=timestamp,
        Open=0,
        High=0,
        Low=0,
        Close=0,
        Volume=0
    )