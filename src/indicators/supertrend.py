import pandas as pd
import pandas_ta as ta

from core.series import Series

class Supertrend:
    def __init__(self, time_series, atr_length=10, multiplier=3.0):
        self.time_series = time_series
        self.atr_length = atr_length
        self.multiplier = float(multiplier) # the key below requires this to be a float

        self.supertrend_main = Series("Supertrend", self.time_series)
        self.supertrend_direction = Series("Supertrend direction" , self.time_series)
        self.supertrend_long = Series("Supertrend Long", self.time_series)
        self.supertrend_short = Series("Supertrend Short", self.time_series)

    def populate(self):
        df = self.time_series.df
        self.pandas_supertrend = ta.supertrend(df["High"], df["Low"], df["Close"], length=self.atr_length, multiplier=self.multiplier)
        self.key = f"_{self.atr_length}_{self.multiplier}"

        self.supertrend_main.populate(pd.Series(self.pandas_supertrend["SUPERT" + self.key]))
        self.supertrend_direction.populate(pd.Series(self.pandas_supertrend["SUPERTd" + self.key]))
        self.supertrend_long.populate(pd.Series(self.pandas_supertrend["SUPERTl" + self.key]))
        self.supertrend_short.populate(pd.Series(self.pandas_supertrend["SUPERTs" + self.key]))

    def plotting(self):
        ST_long = pd.DataFrame({
            "Timestamp": self.time_series.df["Timestamp"].values,
            "values": self.pandas_supertrend["SUPERTl" + self.key].values
        })

        ST_short = pd.DataFrame({
            "Timestamp": self.time_series.df["Timestamp"].values,
            "values": self.pandas_supertrend["SUPERTs" + self.key].values
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
                    "color": "#4ECDC4",
                    "lineWidth": 2
                }
            })

        return plots


    # def plotting(self):
    #     ST_long = pd.DataFrame({
    #         "Timestamp": self.time_series.df["Timestamp"].values,
    #         "values": self.pandas_supertrend["SUPERTl" + self.key].values
    #     })

    #     ST_short = pd.DataFrame({
    #         "Timestamp": self.time_series.df["Timestamp"].values,
    #          "values": self.pandas_supertrend["SUPERTs" + self.key].values
    #     })

    #     return [
    #         {
    #             "name": "ST Long",
    #             "data": ST_long,
    #             "style": {'color': '#FF6B6B', 'lineWidth': 2, 'title': 'ST Long'}
    #         },
    #         {
    #             "name": "ST Short",
    #             "data": ST_short,
    #             "style": {'color': '#4ECDC4', 'lineWidth': 2, 'title': 'ST Short'}
    #         }
    #     ]

    def time_period_met(self):
        return self.supertrend_main.time_period_met()
    
def split_on_nulls(df, value_col):
    """
    Splits a DataFrame into multiple DataFrames
    whenever a null value appears in value_col.
    """
    is_null = df[value_col].isna()

    # Increment segment id whenever we hit a null
    segment_id = is_null.cumsum()

    segments = []
    for _, group in df[~is_null].groupby(segment_id):
        segments.append(group)

    return segments
