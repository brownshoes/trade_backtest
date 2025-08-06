import pandas as pd
import pandas_ta as ta

from core.series import Series

class SimpleMovingAverage:
    def __init__(self, time_series, sma_length=20, smoothing=None):
        self.time_series = time_series
        self.sma_length = sma_length
        self.smoothing = smoothing

        self.sma_name = f"SMA {self.sma_length}"
        self.sma = Series(self.sma_name, self.time_series, smoothing=self.smoothing)

        self.sma_line_color = "black"

    def populate(self):
        sma = ta.sma(self.time_series.df["Close"], self.sma_length)
        self.sma.populate(sma)

    def time_period_met(self):
        return self.sma.time_period_met()
