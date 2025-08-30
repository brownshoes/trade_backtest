
from configs.default_config import default_config

from init.initalization import load_csv, init_backtest_time_series
from init.config import Config

from core.modes.backtest import Backtest

import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)

DEFAULT_CONFIG = default_config

class Container:
    def __init__(self):
        self.curr_df = None
        self.curr_list_of_dict = None

container = Container()

def default_startup():
    df, list_of_dict = load_csv(DEFAULT_CONFIG)
    container.curr_df = df
    container.curr_list_of_dict = list_of_dict

    # Backfill the time_series with historical candle data
    init_backtest_time_series(DEFAULT_CONFIG, list_of_dict)

    # Populate indicators with the initialized time series data
    for indicator in DEFAULT_CONFIG.indicators:
        indicator.populate()

    return container

def flask_backtest(config, df):
    backtest = Backtest(config)
    backtest.execute(df)

    return config
