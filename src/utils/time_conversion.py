import datetime

'''Datetime formats'''
LOGGER_DATETIME_FORMAT = '%Y-%m-%d-%H-%M-%S'
START_END_TIME_FORMAT = "%Y-%m-%d %H:%M"
TIMESTAMP_TO_DATETIME_FORMAT= "%Y-%m-%d, %H:%M:%S %a"

def timestamp_to_datetime(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime(TIMESTAMP_TO_DATETIME_FORMAT)