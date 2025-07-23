import logging
import os

from utils.time_conversion import LOOGER_DATETIME_FORMAT

from logging import StreamHandler
from logging.handlers import RotatingFileHandler

from datetime import datetime

LOGGER_NAME = "my_logger"

def setup_logger(file_name, mode="On"):
    time = datetime.now().strftime(LOOGER_DATETIME_FORMAT)

    megabyte = 1048576 * 10
    log_directory = 'log\\logs'
    log_filename = time + "_" + file_name + '.log'
    log_path = os.path.join(log_directory, log_filename)
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Create the Logger
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)

    # Create the Handler for logging data to a file
    logger_handler = RotatingFileHandler(log_path, maxBytes=megabyte, backupCount=10)
    logger_handler.setLevel(logging.DEBUG)

    # Create the Handler for logging data to console.
    console_handler = StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Disable Logging
    if mode == "OFF":
        logger_handler.setLevel(logging.CRITICAL + 1)
        console_handler.setLevel(logging.CRITICAL + 1)

    # Create a Formatter for formatting the log messages
    logger_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(funcName)s:%(lineno)s] - %(message)s')

    # Add the Formatter to the Handler
    logger_handler.setFormatter(logger_formatter)
    console_handler.setFormatter(logger_formatter)

    # Add the Handler to the Logger
    logger.addHandler(logger_handler)
    logger.addHandler(console_handler)

    return logger