import pandas as pd

import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)

from utils.time_conversion import timestamp_to_datetime
from utils.candle import create_empty_candle, Candle, candle_columns
from utils.calc import most_recent_complete_timestamp


class TimeSeries:
    def __init__(self, candle_size: str):
        self.candle_size_str = candle_size
        self.candle_size = self._parse_candle_size(candle_size) # In minutes
        self.candle_size_seconds = self.candle_size * 60 # used for unix timestamp calculations

        self.df = None
        self.candle_list_dict = []

        self.candle_buffer = []
        self.last_timestamp = None
        self.candle_tick = 60 # Default to a minute
        self.first_candle = True # First candle may not have the correct number of sub candles

        self.time_series_index = 0 

    def update_series(self, namedtuple_candle):
        if self.last_timestamp is None:
            self.last_timestamp = namedtuple_candle.Timestamp

        update_timestamp = namedtuple_candle.Timestamp

        # Missing candles
        if(self.last_timestamp + self.candle_tick < update_timestamp):
            logger.error(
                f"Missing candles from {timestamp_to_datetime(self.last_timestamp + self.candle_tick)} "
                f"to {timestamp_to_datetime(update_timestamp - self.candle_tick)}"
            )

            while(self.last_timestamp + self.candle_tick < update_timestamp):
                self.last_timestamp = self.last_timestamp + self.candle_tick
                empty_candle = create_empty_candle(self.last_timestamp)
                self.candle_buffer.append(empty_candle)
                self._process_candle(empty_candle.Timestamp)

        self.candle_buffer.append(namedtuple_candle)
        self.last_timestamp = namedtuple_candle.Timestamp

        return self._process_candle(update_timestamp)
    
    
    def create_dataframe(self):
        self.df = pd.DataFrame(self.candle_list_dict, columns = candle_columns)
    

    def _process_candle(self, update_timestamp):
        candle_in_progress_timestamp = most_recent_complete_timestamp(update_timestamp, self.candle_size_seconds)
        
        '''If the next tick would belong to the next candle, merge the candles'''
        next_tick_time = update_timestamp + self.candle_tick
        candle_end_time = candle_in_progress_timestamp + self.candle_size_seconds

        if next_tick_time >= candle_end_time:

            #Remove all zero volume candles from candle_buffer
            filtered_buffer = [i for i in self.candle_buffer if i.Volume != 0]
            
            self._error_check(filtered_buffer)

            if not filtered_buffer:
                self.candle_buffer.clear()
                return False

            merged_candle = self._merge_candles(filtered_buffer)

            '''append the merged candle'''
            self.candle_list_dict.append(merged_candle)

            self.candle_buffer.clear()
            self.first_candle = False

            return True
        return False
    

    def _error_check(self, filtered_buffer):
        if not self.first_candle:
            expected_count = int(self.candle_size_seconds / self.candle_tick)
            actual_count = len(self.candle_buffer)
            range_duration = self.candle_buffer[-1].Timestamp - self.candle_buffer[0].Timestamp

            error = False

            if actual_count != expected_count:
                logger.error(f"Incorrect number of candles in buffer: expected {expected_count}, got {actual_count}")
                error = True

            expected_range = self.candle_size_seconds - self.candle_tick
            if range_duration != expected_range:
                logger.error(f"Timestamp mismatch: start={self.candle_buffer[0].Datetime}, end={self.candle_buffer[-1].Datetime}, actual range={range_duration}, expected={expected_range}")
                error = True

            if error:
                logger.error(f"--- Candle Buffer Dump ({actual_count} candles) ---")
                for candle in self.candle_buffer:
                    logger.error(candle)

            # if(len(filtered_list) == 0):
            #     logger.error("Candle Missing: " + self.candle_buffer[0].Datetime)

            # if(len(filtered_list) != len(self.candle_buffer)):
            #     logger.error(self.candle_buffer[0].Datetime + " Valid candles #: " +  str(len(filtered_list)) + " Expected: " + str(self.candle_size_seconds /self.candle_tick)) 


    def _merge_candles(self, filtered_list):
        if not filtered_list:
            raise ValueError("Cannot merge empty candle list.")

        timestamp = most_recent_complete_timestamp(filtered_list[0].Timestamp, self.candle_size_seconds)
        datetime = timestamp_to_datetime(timestamp)

        open_price = float(filtered_list[0].Open)
        close_price = float(filtered_list[-1].Close)
        high = float(filtered_list[0].High)
        low = float(filtered_list[0].Low)
        volume = 0.0

        for row in filtered_list:
            volume += float(row.Volume)
            high = max(high, float(row.High))
            low = min(low, float(row.Low))

        return Candle(datetime, timestamp, open_price, high, low, close_price, volume)


    def _parse_candle_size(self, value: str) -> int:
        """Convert strings like '5m' or '1h' or '1d' to minutes."""
        if value.endswith('m'):
            return int(value[:-1])
        elif value.endswith('h'):
            return int(value[:-1]) * 60
        elif value.endswith('d'):
            return int(value[:-1]) * 60 * 24
        else:
            raise ValueError(f"Invalid candle size: {value}")