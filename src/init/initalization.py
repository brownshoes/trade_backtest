import os
import importlib
import json

from init.config import Config  

from core.modes.backtest import Backtest

from input.csv_input import intake_csv_data, get_buffered_start_time
from utils.candle import Candle

from decorators.timeit import timeit

from database.db_setup import init_db

import logging
from log.logger import LOGGER_NAME, setup_logger
logger = logging.getLogger(LOGGER_NAME)

import jsonpickle

from configs.create_config import create_config_from_json, config_to_json


directories = ["log\\logs"]

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

    # After filling the time_series, create/fill the dataframe
    for time_series in config.time_series:
        time_series.create_dataframe()
        logger.info(time_series.df)

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
    
@timeit
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

    backtest = Backtest(config)
    backtest.execute(df)

@timeit
def flask_init():
    config_module_name = "configs.test"
    #setup_logger("flask")
    create_directories()
    config = load_config(config_module_name)
    backtest_init(config)

def test_config_storage(config):
    json = config.to_json()
    print(json)

    # Encode the object
    json_str = jsonpickle.encode(config, indent=4)
    print(json_str)

    obj_restored = jsonpickle.decode(json_str)
    print(obj_restored.name) 

def init_test(file_name):
        with open(file_name, 'r') as f:
            json_data = json.load(f)


        config = create_config_from_json(json_data)
        print(config.to_json())
        setup_logger(config.name, mode="off")

        create_directories()
        backtest_init(config)

def init_test2(config_module_name: str):

    setup_logger(config_module_name, mode="off")

    init_db()
    
    create_directories()
    config = load_config(config_module_name)

    json_config = config_to_json(config)
    print(json.dumps(json_config, default=str, indent=4))

    config_from_json = create_config_from_json(json_config)

    create_directories()
    backtest_init(config_from_json)


def init(config_module_name: str):
    """
    Entry point initialization: setup logger, directories, load config, database.
    """
    setup_logger(config_module_name, mode="off")

    init_db()
    
    create_directories()
    config = load_config(config_module_name)
    test_config_storage(config)


    # backtest_init(config)
    # return config