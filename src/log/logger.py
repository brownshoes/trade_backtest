import logging
import os
import re
from datetime import datetime
from logging import StreamHandler
from logging.handlers import RotatingFileHandler

from utils.time_conversion import LOGGER_DATETIME_FORMAT  # Make sure this exists

LOGGER_NAME = "my_logger"

def setup_logger(file_name, mode="On"):
    # Helper to strip ANSI escape codes (e.g., color codes)
    def remove_ansi_codes(text) -> str:
        text = str(text)  # Convert objects like DataFrames to string
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    # Custom Formatter that strips ANSI codes from formatted log message
    class PlainTextFormatter(logging.Formatter):
        def format(self, record):
            original_msg = super().format(record)
            return remove_ansi_codes(original_msg)

    # Generate a timestamped log file name
    time = datetime.now().strftime(LOGGER_DATETIME_FORMAT)

    # Define log file path
    max_log_size = 10 * 1024 * 1024  # 10 MB
    log_directory = os.path.join('log', 'logs')
    log_filename = f"{time}_{file_name}.log"
    log_path = os.path.join(log_directory, log_filename)

    # Create the log directory if it doesn't exist
    os.makedirs(log_directory, exist_ok=True)

    # Create or get the named logger
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)  # Capture all log levels

    # Clear old handlers to prevent duplicate logs if setup_logger is called again
    if logger.hasHandlers():
        logger.handlers.clear()

    # File handler (rotating)
    file_handler = RotatingFileHandler(
        log_path, maxBytes=max_log_size, backupCount=10, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # Console handler
    console_handler = StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Disable logging output if mode is OFF
    if mode.lower() == "off":
        file_handler.setLevel(logging.CRITICAL)
        console_handler.setLevel(logging.CRITICAL)

    # Format string for both handlers
    log_format = '%(asctime)s - %(levelname)s - [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s'

    # Apply formatters
    file_formatter = PlainTextFormatter(log_format)
    console_formatter = logging.Formatter(log_format)

    file_handler.setFormatter(file_formatter)       # ANSI codes removed
    console_handler.setFormatter(console_formatter) # ANSI codes retained (for colors)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
