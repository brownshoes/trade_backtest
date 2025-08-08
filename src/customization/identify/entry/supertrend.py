'''Entry identified when a long is beginning'''
class SupertrendEntry:
    def __init__(self, supertrend):
        self.supertrend = supertrend
        self.time_series = supertrend.time_series

    def identify_entry(self):
        if not self.supertrend.time_period_met():
            return False

        index = self.time_series.time_series_index

        last = self.supertrend.supertrend_direction.get_index(index - 1)
        current = self.supertrend.supertrend_direction.get_index(index)

        return last == -1 and current == 1
