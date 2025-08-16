import time

import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)


def timeit(func):
    """Decorator to measure execution time of a function."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.critical(f"Function `{func.__name__}` executed in {end - start:.4f} seconds")
        return result
    return wrapper
