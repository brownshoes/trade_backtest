import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)


def backtest(self, df):
    logger.info(df)

    '''Convert time_series Timestamp column to a list. This MASSIVELY improves speed'''
    list_timestamp = {} #the timestamp list of a time_series
    for time_series in self.time_series_list:
        # logger.info(str(time_series.candle_size) + " " + str(len(time_series.candle_list_dict)) + " " + time_series.candle_list_dict[0]["Datetime"])
        list_timestamp[time_series] = time_series.df["Timestamp"].tolist()

    timestamps = df["Timestamp"].to_numpy()
    opens = df["Open"].to_numpy()

    for i in range(len(df)):
        '''Treat the current state as the start of the candle. Ex: At 1200, the price is 'X'. Hence use open price'''
        self.state_obj.update_current_price_timestamp(opens[i], timestamps[i])
        # self.state_obj.update_state_pre(timestamps[i]) Why does this exist
        self.state_obj.check_orders_for_execution()
        self.trading_strategy.check_open_orders_for_completion(self.state_obj)
        self.limit_adjust.adjust_limit_orders(self.trading_strategy.placeBuy, self.trading_strategy.placeSell, self.state_obj, self.trading_strategy.strategies_buy, self.trading_strategy.strategies_sell)


        '''
        Check each time_series and see if the current timestamp matches the next timestamp in the time_series.
        If it matches, we've reached the next candle in the time_series, meaning it's been updated
        '''
        timestamp = timestamps[i]
        time_series_updated = []
        for time_series in self.time_series_list:
            timestamp_list = list_timestamp[time_series]

            '''Prevent index 'out of bounds' '''
            if(time_series.time_series_index + 2 >= len(timestamp_list)):
                continue

            '''
            Consider time_series updated if we have reached the end time of the current index.
            Ex: 5 minute candle -> Begins at 12:00, we should consider it updated/complete at the 12:05 minute candle
            Ex: 5 minute candle -> At timestamp 12:07, the index should be at the 12:00 candle
            A live intake would update at 12:04 candle, since the candle would be complete at 12:05
            '''
            if(timestamp >= timestamp_list[time_series.time_series_index + 1] + time_series.candle_size_seconds):
                time_series_updated.append(time_series)
                time_series.time_series_index = time_series.time_series_index + 1

            
            # logger.info("SIZE: " + time_series.candle_string)
            # logger.info("Current Timestamp: " + utils.convert_time(namedtuple_candle.Timestamp))
            # logger.info("Index Timestamp: " + utils.convert_time(timestamp_list[time_series.time_series_index]))
            # logger.info("Update Timestamp: " + utils.convert_time(timestamp_list[time_series.time_series_index + 1]  + time_series.candle_size_seconds))
            # logger.info(str(time_series.candle_size_seconds) + " " + str(time_series.time_series_index) + " " + time_series.candle_list_dict[time_series.time_series_index]["Datetime"] + " " + utils.convert_time(namedtuple_candle.Timestamp))


        '''If a time_series was updated, execute trading_strategy'''
        if(timestamps[i] >= self.time_series_list[0].start_unix and 
            len(time_series_updated) != 0 and self.trading_strategy != None and self.min_num_candles_buffered):
            self.trading_strategy.execute_trading_strategy(self.state_obj, time_series_updated)
            self.state_obj.check_orders_for_execution()
            self.trading_strategy.check_open_orders_for_completion(self.state_obj)

        '''Check here following the increment of the index. Takes effect the next iteration'''
        self._check_min_num_of_candles()

        self.state_obj.update_state_post(time_series_updated)
        self.update_current_performance(timestamp)