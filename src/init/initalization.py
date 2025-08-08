import os
import importlib

from init.config import Config  

from input.csv_input import intake_csv_data, get_buffered_start_time
from utils.candle import Candle

from decorators.timeit import timeit

import logging
from log.logger import LOGGER_NAME, setup_logger
logger = logging.getLogger(LOGGER_NAME)


directories = ["save_states", "logs", "csv_record", "cred"]

def create_directories():
    """
    Ensure all required directories exist.
    """
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

def load_config(config_module_name: str) -> Config:
    """
    Dynamically load a config module and return its 'config' attribute.
    """
    try:
        module = importlib.import_module(config_module_name)
        return module.config
    except (ModuleNotFoundError, AttributeError) as e:
        raise ImportError(f"Could not load config from {config_module_name}: {e}")

def dict_to_candle(d: dict) -> Candle:
    """
    Convert a dictionary representing a candle to a Candle object.
    """
    return Candle(
        d["Datetime"], d["Timestamp"], d["Open"], d["High"], d["Low"], d["Close"], d["Volume"]
    )

@timeit
def init_backtest_time_series(config: Config, list_of_dict: list):
    """
    Feed historical candle data into each time series for backtesting initialization.
    """
    for candle_dict in list_of_dict:
        candle = dict_to_candle(candle_dict)
        for time_series in config.time_series:
            time_series.update_series(candle)

@timeit
def load_csv(config: Config):
    """
    Load historical data for backtesting based on buffered start time.
    """
    if config.mode == "BACKTEST":
        buffered_start_time = get_buffered_start_time(config.start_time, config.time_series)
        logger.info(f"Buffered start time: {buffered_start_time}")
        df, list_of_dict = intake_csv_data(config.csv_input_file, buffered_start_time, config.end_time)
        return df, list_of_dict

def backtest_init(config: Config):
    """
    Initialize backtest: load CSV data, backfill time series, and populate indicators.
    """
    df, list_of_dict = load_csv(config)

    # Backfill the time_series with historical candle data
    init_backtest_time_series(config, list_of_dict)

    # Populate indicators with the initialized time series data
    for indicator in config.indicators:
        indicator.populate()

def init(config_module_name: str):
    """
    Entry point initialization: setup logger, directories, and load config.
    """
    setup_logger(config_module_name)
    create_directories()
    config = load_config(config_module_name)
    return config