from flask import Flask, render_template, jsonify
import csv

from init.initalization import flask_init
from init.flask_init import default_startup, container, flask_backtest, DEFAULT_CONFIG

from core.position_tracking.statistics import Statistics



from log.logger import setup_logger
#from log.logger import setup_logger
log = setup_logger("Flask", mode="one")
default_startup()

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

@app.route('/report')
def closed_position_view_report():
    config = flask_backtest(DEFAULT_CONFIG, container.curr_df)
    trading_state = config.trading_state
    closed_positions = [
        cp.to_dict() for cp in trading_state.closed_positions
    ]
    statistics = Statistics(trading_state, config.main_time_series.candle_size)
    metrics = statistics.to_dict()
    return render_template('report.html', positions=closed_positions, metrics=metrics)

@app.route('/closed-position')
def closed_position_view():
    config = flask_backtest(DEFAULT_CONFIG, container.curr_df)
    trading_state = config.trading_state
    closed_positions = [
        cp.to_dict() for cp in trading_state.closed_positions
    ]
    return render_template('closed_position.html', positions=closed_positions)


@app.route("/")
def index():
    return render_template("index.html")

# @app.route("/ohlc")
# def ohlc():
#     return jsonify(load_data())



if __name__ == "__main__":
    app.run(debug=True)
