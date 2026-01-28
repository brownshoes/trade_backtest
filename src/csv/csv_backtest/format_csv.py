import pandas as pd

# Read input CSV
df = pd.read_csv("processed_trading_data2.csv")

# Convert timestamp from ms to seconds
df["Timestamp"] = df["timestamp"] / 1000.0

# Parse datetime column
dt = pd.to_datetime(df["datetime"], utc=True)

# Format Datetime column like: "12/31/2023, 17:01:00 Sun"
df["Datetime"] = dt.dt.strftime("%m/%d/%Y, %H:%M:%S %a")

# Rename price/volume columns
df = df.rename(columns={
    "open": "Open",
    "high": "High",
    "low": "Low",
    "close": "Close",
    "volume": "Volume"
})

# Select and order final columns
df = df[[
    "Datetime",
    "Timestamp",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume"
]]

# Save to output CSV
df.to_csv("processed_btc_full.csv", index=False)
