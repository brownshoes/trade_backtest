import pandas as pd
import pandas_ta as ta

from core.series import Series

from numpy import nan as npNaN
from pandas import DataFrame
from pandas_ta.overlap import hl2
from pandas_ta.volatility import atr
from pandas_ta.utils import get_offset, verify_series

from indicators.indicator_utils import split_on_nulls
from indicators.moving_averages import get_ma

class SupertrendMA:
    def __init__(self, time_series, atr_length=10, multiplier=3.0, ma_length = 100, moving_average_type=None):
        self.time_series = time_series
        self.atr_length = atr_length
        self.multiplier = float(multiplier) # the key below requires this to be a float
        self.ma_length = ma_length
        self.ta_moving_average = self.ta_moving_average = get_ma(moving_average_type)

        self.supertrend_ma_main = Series("Supertrend MA", self.time_series)
        self.supertrend_ma_direction = Series("Supertrend MA direction" , self.time_series)
        self.supertrend_ma_long = Series("Supertrend MA Long", self.time_series)
        self.supertrend_ma_short = Series("Supertrend MA Short", self.time_series)

    def populate(self):
        df = self.time_series.df
        self.pandas_supertrend_ma = self._supertrend(df["High"], df["Low"], df["Close"])

        self.key = f"_{self.atr_length}_{self.multiplier}"

        self.supertrend_ma_main.populate(pd.Series(self.pandas_supertrend_ma["SUPERT" + self.key]))
        self.supertrend_ma_direction.populate(pd.Series(self.pandas_supertrend_ma["SUPERTd" + self.key]))
        self.supertrend_ma_long.populate(pd.Series(self.pandas_supertrend_ma["SUPERTl" + self.key]))
        self.supertrend_ma_short.populate(pd.Series(self.pandas_supertrend_ma["SUPERTs" + self.key]))

    def _supertrend(self, high, low, close, length=None, multiplier=None, offset=None, **kwargs):
        """Indicator: Supertrend"""
        # Validate Arguments
        #length = int(length) if length and length > 0 else 7
        length = self.atr_length
        #multiplier = float(multiplier) if multiplier and multiplier > 0 else 3.0
        multiplier = self.multiplier
        high = verify_series(high, length)
        low = verify_series(low, length)
        close = verify_series(close, length)
        offset = get_offset(offset)

        if high is None or low is None or close is None: return

        # Calculate Results
        m = close.size
        dir_, trend = [1] * m, [0] * m
        long, short = [npNaN] * m, [npNaN] * m

        #hl2_ = hl2(high, low)
        matr = multiplier * atr(high, low, close, length)
        moving_avg = self.ta_moving_average(close, length = self.ma_length)
        upperband = moving_avg + matr
        lowerband = moving_avg - matr

        for i in range(1, m):
            if close.iloc[i] > upperband.iloc[i - 1]:
                dir_[i] = 1
            elif close.iloc[i] < lowerband.iloc[i - 1]:
                dir_[i] = -1
            else:
                dir_[i] = dir_[i - 1]
                if dir_[i] > 0 and lowerband.iloc[i] < lowerband.iloc[i - 1]:
                    lowerband.iloc[i] = lowerband.iloc[i - 1]
                if dir_[i] < 0 and upperband.iloc[i] > upperband.iloc[i - 1]:
                    upperband.iloc[i] = upperband.iloc[i - 1]

            if dir_[i] > 0:
                trend[i] = long[i] = lowerband.iloc[i]
            else:
                trend[i] = short[i] = upperband.iloc[i]

        # Prepare DataFrame to return
        _props = f"_{length}_{multiplier}"
        df = DataFrame({
                f"SUPERT{_props}": trend,
                f"SUPERTd{_props}": dir_,
                f"SUPERTl{_props}": long,
                f"SUPERTs{_props}": short,
            }, index=close.index)

        df.name = f"SUPERT{_props}"
        df.category = "overlap"

        # Apply offset if needed
        if offset != 0:
            df = df.shift(offset)

        # Handle fills
        if "fillna" in kwargs:
            df.fillna(kwargs["fillna"], inplace=True)

        if "fill_method" in kwargs:
            df.fillna(method=kwargs["fill_method"], inplace=True)

        return df
    
    def plotting(self):
        ST_long = pd.DataFrame({
            "Timestamp": self.time_series.df["Timestamp"].values,
            "values": self.pandas_supertrend_ma["SUPERTl" + self.key].values
        })

        ST_short = pd.DataFrame({
            "Timestamp": self.time_series.df["Timestamp"].values,
            "values": self.pandas_supertrend_ma["SUPERTs" + self.key].values
        })

        plots = []

        # --- ST Long segments ---
        for i, segment in enumerate(split_on_nulls(ST_long, "values")):
            plots.append({
                "name": f"ST Long {i}",
                "data": segment,
                "style": {
                    "color": "#FF6B6B",
                    "lineWidth": 2
                }
            })

        # --- ST Short segments ---
        for i, segment in enumerate(split_on_nulls(ST_short, "values")):
            plots.append({
                "name": f"ST Short {i}",
                "data": segment,
                "style": {
                    "color": "#53CD08",
                    "lineWidth": 2
                }
            })

        return plots


    def time_period_met(self):
        return self.supertrend_ma_main.time_period_met()