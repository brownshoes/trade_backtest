from flask import Flask, render_template, jsonify
import csv
from datetime import datetime

app = Flask(__name__)

def calculate_sma(data, period=5):
    sma = []
    closes = [row['close'] for row in data]
    for i in range(len(closes)):
        if i < period - 1:
            sma.append(None)
        else:
            avg = sum(closes[i - period + 1:i + 1]) / period
            sma.append(round(avg, 2))
    return sma

def load_data():
    ohlc_data = []
    with open("csv\\csv_backtest\\short_btc.csv", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ohlc_data.append({
                "time": int(float(row["Timestamp"])),  # UNIX timestamp (seconds)
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
            })

    sma_values = calculate_sma(ohlc_data, period=5)

    sma_data = [
        {"time": row["time"], "value": sma}
        for row, sma in zip(ohlc_data, sma_values)
        if sma is not None  # Remove initial nulls for chart clarity
    ]

    return {
        "ohlc": ohlc_data,
        "sma": sma_data
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ohlc")
def ohlc():
    return jsonify(load_data())

if __name__ == "__main__":
    app.run(debug=True)


