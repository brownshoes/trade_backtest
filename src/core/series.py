import pandas as pd
import pandas_ta as ta

class Series:
    def __init__ (self, name, time_series, smoothing = None):
        self.name = name
        self.series = pd.Series()
        self.time_series = time_series
        self.smoothing = smoothing

    def populate(self, series):
        if(self.smoothing == None):
            self.series = series
        elif(self.smoothing == "rma"):
            self.series = ta.rma(series)
        else:
            raise ValueError("smoothing value incorrectly set")

    def time_period_met(self):
        if(self.time_series.time_series_index >= self.series.first_valid_index()):
            return True
        return False

    def length(self):
        return len(self.series) - self.series.first_valid_index()

    def get_curr(self):
        return self.series.iloc[self.time_series.time_series_index]

    def get_index(self, index):
        return self.series.iloc[index]

    def get_series(self):
            return self.series