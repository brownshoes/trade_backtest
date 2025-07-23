import pandas as pd

df = pd.read_csv("csv\\csv_backtest\\formatted_btc_usd_patch.csv")

# Convert cutoff_date to Unix timestamp (seconds since epoch)
cutoff_date = pd.to_datetime("2024-01-01")
cutoff_timestamp = cutoff_date.timestamp()

# Filter rows where Timestamp > cutoff timestamp (both floats)
df_after = df[df['Timestamp'] > cutoff_timestamp]

df_after.to_csv("short_btc.csv", index=False)

print(f"Saved {len(df_after)} rows after {cutoff_date.date()} to 'short_btc.csv'")


