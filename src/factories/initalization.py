import os
import importlib

from factories.config import Config  

from input.csv_input import intake_csv_data, get_buffered_start_time
from utils.candle import Candle

from decorators.timeit import timeit

import logging
from log.logger import LOGGER_NAME, setup_logger
logger = logging.getLogger(LOGGER_NAME)

directories = ["save_states", "logs", "csv_record", "cred"]

def backtest_init(config):
    df, list_of_dict = load_csv(config)

    #backfill the time_series 
    init_backtest_time_series(config, list_of_dict)

    for indicator in config.indicators:
        indicator.populate()





@timeit
def init_backtest_time_series(config, list_of_dict):
    for candle_dict in list_of_dict:
        candle = dict_to_candle(candle_dict)
        for time_series in config.time_series:
            time_series.update_series(candle)

def dict_to_candle(d: dict) -> Candle:
    return Candle(
        d["Datetime"], d["Timestamp"], d["Open"], d["High"], d["Low"], d["Close"], d["Volume"]
    )

def load_config(config_module_name: str) -> Config:
    try:
        module = importlib.import_module(config_module_name)
        return module.config
    except (ModuleNotFoundError, AttributeError) as e:
        raise ImportError(f"Could not load config from {config_module_name}: {e}")

def create_directories():
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

def load_csv(config):
    if config.mode == "BACKTEST":
        bufferd_start_time = get_buffered_start_time(config.start_time, config.time_series)
        logger.info(f"Buffered start time: {bufferd_start_time}")
        df, list_of_dict = intake_csv_data(config.csv_input_file, bufferd_start_time, config.end_time)
        return df, list_of_dict


def init(config_module_name):
    setup_logger(config_module_name)
    create_directories()
    config = load_config(config_module_name)




    # create_directories()