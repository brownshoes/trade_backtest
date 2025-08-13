from init.config import Config
from decorators.timeit import timeit

from utils.time_conversion import START_END_TIME_FORMAT

import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)

class Backtest:
    def __init__(self, config: 'Config'):
        # Store config reference
        self.config = config

        # Time series data
        self.time_series_list = config.time_series

        # Exchange & trading state
        self.exg_state = config.exg_state
        self.trading_state = config.trading_state

        # Trading strategy components
        self.trading = config.trading
        self.buy_strategy = config.buy_strategy
        self.sell_strategy = config.sell_strategy

        # Execution client (e.g. mock or real exchange interface)
        self.client = config.client

        # Limit order adjustment logic
        self.limit_adjust = config.limit_adjust

        # Candle buffering controls
        self.min_num_candles_buffered = False
        self.min_num_of_candles_required = 199

        # Backtest time range (Unix timestamps)
        self.start_unix = config.start_unix
        self.end_unix = config.end_unix


    @timeit
    def execute(self, df):
        logger.info(df)

        '''Convert time_series Timestamp column to a list. This MASSIVELY improves speed'''
        list_timestamp = {} #the timestamp list of a time_series
        for time_series in self.time_series_list:
            # logger.info(str(time_series.candle_size) + " " + str(len(time_series.candle_list_dict)) + " " + time_series.candle_list_dict[0]["Datetime"])
            #list_timestamp[time_series] = time_series.df["Timestamp"].tolist()
            list_timestamp[time_series] = time_series.df["Timestamp"].to_numpy()

        timestamps = df["Timestamp"].to_numpy()
        opens = df["Open"].to_numpy()

        for i in range(len(df)):
            '''Treat the current state as the start of the candle. Ex: At 1200, the price is 'X'. Hence use open price'''
            self.exg_state.update_current_price_timestamp(opens[i], timestamps[i])
            self.client.check_orders_for_execution()
            self.trading.check_open_orders_for_completion(self.exg_state)
            self.limit_adjust.adjust_limit_orders(self.trading.placeBuy, self.trading.placeSell, self.exg_state, self.trading_state, self.buy_strategy, self.sell_strategy)

            '''
            Check each time_series and see if the current timestamp matches the next timestamp in the time_series.
            If it matches, we've reached the next candle in the time_series, meaning it's been updated
            '''
            timestamp = timestamps[i]
            time_series_updated = []
            for time_series in self.time_series_list:
                timestamp_numpy = list_timestamp[time_series]

                '''Prevent index 'out of bounds' '''
                if(time_series.time_series_index + 2 >= len(timestamp_numpy)):
                    continue

                '''
                Consider time_series updated if we have reached the end time of the current index.
                Ex: 5 minute candle -> Begins at 12:00, we should consider it updated/complete at the 12:05 minute candle
                Ex: 5 minute candle -> At timestamp 12:07, the index should be at the 12:00 candle
                A live intake would update at 12:04 candle, since the candle would be complete at 12:05
                '''
                if(timestamp >= timestamp_numpy[time_series.time_series_index + 1] + time_series.candle_size_seconds):
                    time_series_updated.append(time_series)
                    time_series.time_series_index = time_series.time_series_index + 1

                
                # logger.info("SIZE: " + time_series.candle_string)
                # logger.info("Current Timestamp: " + utils.convert_time(namedtuple_candle.Timestamp))
                # logger.info("Index Timestamp: " + utils.convert_time(timestamp_list[time_series.time_series_index]))
                # logger.info("Update Timestamp: " + utils.convert_time(timestamp_list[time_series.time_series_index + 1]  + time_series.candle_size_seconds))
                # logger.info(str(time_series.candle_size_seconds) + " " + str(time_series.time_series_index) + " " + time_series.candle_list_dict[time_series.time_series_index]["Datetime"] + " " + utils.convert_time(namedtuple_candle.Timestamp))


            '''If a time_series was updated, execute trading_strategy'''
            if self.min_num_candles_buffered and time_series_updated and timestamp >= self.start_unix:
                self.trading.execute_trading_strategy(self.exg_state, time_series_updated)
                self.client.check_orders_for_execution()
                self.trading.check_open_orders_for_completion(self.exg_state)

            '''Check here following the increment of the index. Takes effect the next iteration'''
            self._check_min_num_of_candles()
            self.exg_state.validate_exchange_state()

    def _check_min_num_of_candles(self):
        if not self.min_num_candles_buffered:
            min_index_required = self.min_num_of_candles_required - 1

            for time_series in self.time_series_list:
                if time_series.time_series_index < min_index_required:
                    return

            for time_series in self.time_series_list:
                entry = time_series.candle_list[time_series.time_series_index]

                logger.info(
                    f"\n  Min number of candles reached: {time_series.candle_size_str}\n"
                    f"  Time:          {entry.Timestamp} | {entry.Datetime}\n"
                    f"  Candles:       {len(time_series.candle_list)} | Index: {time_series.time_series_index}"
                )
                # logger.info(
                #     f"Min number of candles reached: {time_series.candle_list[time_series.time_series_index].Timestamp} "
                #     f"{time_series.candle_list[time_series.time_series_index].Datetime} "
                #     f"{len(time_series.candle_list)} {time_series.time_series_index}"
                # )



            self.min_num_candles_buffered = True
