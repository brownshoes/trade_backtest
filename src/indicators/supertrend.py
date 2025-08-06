import pandas as pd
import pandas_ta as ta

from core.series import Series

class Supertrend:
    def __init__(self, time_series, atr_length=10, multiplier=3.0):
        self.time_series = time_series
        self.atr_length = atr_length
        self.multiplier = multiplier

        self.supertrend_main = Series("Supertrend", self.time_series)
        self.supertrend_direction = Series("Supertrend direction" , self.time_series)
        self.supertrend_long = Series("Supertrend Long", self.time_series)
        self.supertrend_short = Series("Supertrend Short", self.time_series)

    def populate(self):
        df = self.time_series.df
        pandas_supertrend = ta.supertrend(df["High"], df["Low"], df["Close"], length=self.atr_length, multiplier=self.multiplier)

        key = f"_{self.atr_length}_{self.multiplier}"

        self.supertrend_main.populate(pd.Series(pandas_supertrend["SUPERT" + key]))
        self.supertrend_direction.populate(pd.Series(pandas_supertrend["SUPERTd" + key]))
        self.supertrend_long.populate(pd.Series(pandas_supertrend["SUPERTl" + key]))
        self.supertrend_short.populate(pd.Series(pandas_supertrend["SUPERTs" + key]))

    def time_period_met(self):
        return self.supertrend_main.time_period_met()