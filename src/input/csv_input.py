import pandas as pd
from datetime import datetime, timedelta

from utils.time_conversion import START_END_TIME_FORMAT

import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)

def intake_csv_data(csv_file: str, start_time: str, end_time: str) -> tuple[pd.DataFrame, list[dict]]:
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file}")
        raise
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise


    start_unix = datetime.strptime(start_time, START_END_TIME_FORMAT).timestamp()
    end_unix = datetime.strptime(end_time, START_END_TIME_FORMAT).timestamp()

    # Filter the DataFrame based on timestamp range
    df = df[(df['Timestamp'] >= start_unix) & (df['Timestamp'] <= end_unix)]

    if df.empty:
        logger.error(f"No data found in the specified time range: {start_time} <-> {end_time}")
        raise ValueError(f"No data found in the specified time range: {start_time} <-> {end_time}")

    # Logging first and last row information
    first_row = df.iloc[0]
    last_row = df.iloc[-1]
    logger.info(f"Beginning row -> Datetime: {first_row['Datetime']} Timestamp: {first_row['Timestamp']}")
    logger.info(f"Ending row -> Datetime: {last_row['Datetime']} Timestamp: {last_row['Timestamp']}")
    logger.info(f"Total rows: {df.shape[0]}")

    # Convert to list of dicts
    row_dicts = df.to_dict(orient="records")

    return df, row_dicts


def get_buffered_start_time(start_time: str, time_series_list) -> str:
    """
    Calculates the earliest buffered start time from a given start_time and a list of time_series.

    Args:
        start_time (str): Datetime string in format "YYYY-MM-DD HH:MM"
        time_series_list (list): List of time_series objects with:
            - candle_size (int): candle size in minutes

    Returns:
        str: Earliest buffered start time as "YYYY-MM-DD HH:MM"
    """

    DEFAULT_NUM_CANDLES = 1500

    if not time_series_list:
        raise ValueError("time_series_list cannot be empty")

    start_dt = datetime.strptime(start_time, START_END_TIME_FORMAT)

    earliest_buffered_time = datetime.max

    for ts in time_series_list:
        buffer = timedelta(seconds=ts.candle_size * DEFAULT_NUM_CANDLES)
        buffered_start = start_dt - buffer

        if buffered_start < earliest_buffered_time:
            earliest_buffered_time = buffered_start

    return earliest_buffered_time.strftime(START_END_TIME_FORMAT)


