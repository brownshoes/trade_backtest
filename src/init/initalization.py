import os
import importlib
import json

from init.config import Config  

from core.modes.backtest import Backtest

from input.csv_input import read_csv_file, parse_csv_data, get_buffered_start_time
from utils.candle import Candle

from decorators.timeit import timeit

from database.db_setup import init_db

import logging
from log.logger import LOGGER_NAME, setup_logger
logger = logging.getLogger(LOGGER_NAME)

import jsonpickle

import pandas as pd

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


csv_cache = {
    "file_name": None,
    "df": None,
}

# Cache for filtered CSV results
_filter_cache = {
    "csv_file": None,
    "start_time": None,
    "end_time": None,
    "df_filtered": None,
    "row_dicts": None,
}

def load_csv_file(csv_file: str) -> pd.DataFrame:
    """
    Pure CSV reading from disk.
    Caches the DataFrame if the file name matches.
    """
    if csv_cache.get("file_name") == csv_file and csv_cache.get("df") is not None:
        logger.critical(f"📄 Reusing cached CSV: {csv_file}")
        return csv_cache["df"]

    logger.info(f"📄 Reading CSV from disk: {csv_file}")
    df = read_csv_file(csv_file)  # your original I/O function
    csv_cache["file_name"] = csv_file
    csv_cache["df"] = df
    return df

def filter_csv_by_time(df: pd.DataFrame, start_time: str, end_time: str, csv_file: str) -> tuple[pd.DataFrame, list[dict]]:
    """
    Filters the given DataFrame by start and end time and converts it to a list of dicts.
    Uses a cache keyed by CSV file name and time range.
    Since the start time is based on the buffered start time, changes in the candle size will result 
    in a new start_time.
    """
    # Check if cached result exists
    if (
        _filter_cache.get("csv_file") == csv_file and
        _filter_cache.get("start_time") == start_time and
        _filter_cache.get("end_time") == end_time
    ):
        logger.critical(f"📄 Reusing cached filtered CSV for {csv_file}")
        return _filter_cache["df_filtered"], _filter_cache["row_dicts"]

    # Filter using parse_csv_data
    df_filtered, row_dicts = parse_csv_data(df, start_time, end_time)

    # Update cache
    _filter_cache.update({
        "csv_file": csv_file,
        "start_time": start_time,
        "end_time": end_time,
        "df_filtered": df_filtered,
        "row_dicts": row_dicts,
    })

    return df_filtered, row_dicts


@timeit
def load_csv(config: Config):
    """
    Load CSV for backtesting:
    1. Use cached CSV if available
    2. Determine buffered start time
    3. Parse/filter CSV
    """
    if config.mode != "BACKTEST":
        return None, None

    df_csv = load_csv_file(config.csv_input_file)
    buffered_start_time = get_buffered_start_time(config.start_time, config.time_series)
    logger.info(f"Buffered start time: {buffered_start_time}")

    df, list_of_dict = filter_csv_by_time(df_csv, buffered_start_time, config.end_time, config.csv_input_file)
    return df, list_of_dict

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