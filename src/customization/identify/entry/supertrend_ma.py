import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)


'''Entry identified when a long is beginning'''
class SupertrendMAEntry:
    def __init__(self, supertrendMA):
        self.supertrendMA = supertrendMA
        self.time_series = supertrendMA.time_series

    def identify_entry(self):
        if not self.supertrendMA.time_period_met():
            return False

        index = self.time_series.time_series_index

        last = self.supertrendMA.supertrend_ma_direction.get_index(index - 1)
        current = self.supertrendMA.supertrend_ma_direction.get_index(index)

        # Debug
        main = self.supertrendMA.supertrend_ma_main.get_index(index)
        long = self.supertrendMA.supertrend_ma_long.get_index(index)
        short = self.supertrendMA.supertrend_ma_short.get_index(index)

        logger.debug(f"Main: {main} Direction: {current} Long: {long} Short: {short}")

        return last == -1 and current == 1
