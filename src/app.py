from flask import Flask, render_template, request, jsonify, render_template_string
import json

import pandas as pd

from indicators.indicator_classes import INDICATOR_CLASSES
from customization.customization_classes import IDENTIFY_ENTRY_CLASSES, IDENTIFY_EXIT_CLASSES, ENTRY_TRADE_CONDITIONS_CLASSES,EXIT_TRADE_CONDITIONS_CLASSES,BUY_STRATEGIES_CLASSES, SELL_STRATEGIES_CLASSES, EXIT_STRATEGIES_CLASSES

from init.initalization import backtest_init
from configs.create_config import create_config_from_json
from core.position_tracking.statistics import Statistics

from log.logger import setup_logger
log = setup_logger("Flask", mode="Off")

app = Flask(__name__)

data_store = []

@app.route('/')
def index():
    return render_template('layout.html',
        indicators=INDICATOR_CLASSES,
        identify_entry_classes=IDENTIFY_ENTRY_CLASSES,
        identify_exit_classes=IDENTIFY_EXIT_CLASSES,
        entry_trade_conditions_classes=ENTRY_TRADE_CONDITIONS_CLASSES,
        exit_trade_conditions_classes=EXIT_TRADE_CONDITIONS_CLASSES,
        buy_strategies_classes=BUY_STRATEGIES_CLASSES,
        sell_strategies_classes=SELL_STRATEGIES_CLASSES,
        exit_strategies_classes=EXIT_STRATEGIES_CLASSES)

@app.route('/create_edit', methods=['GET', 'POST'])
def create_edit():
    if request.method == 'POST':
        data = request.form.to_dict()
        # Process the submitted config here
        return jsonify({"success": True, "data": data})
    return render_template(
        'create_edit.html'
    )

@app.route('/load')
def tab_load():
    return render_template('load.html', data=data_store)

@app.route('/create_edit', methods=['GET', 'POST'])
def tab_create_edit():
    if request.method == 'POST':
        item = request.form.get('item')
        if item:
            data_store.append(item)
            return jsonify(success=True)
        return jsonify(success=False)
    return render_template('create_edit.html')

@app.route('/results')
def tab_results():
    return render_template('results.html', data=data_store)

@app.route("/submit", methods=["POST"])
def submit():
    json_data = request.get_json()
    log.info(f"📦 Received data:\n{json.dumps(json_data, indent=4)}")

    # === 1. Build and run backtest ===
    config = create_config_from_json(json_data)
    log.info(config)
    backtest_init(config)

    trading_state = config.trading_state
    closed_positions = trading_state.closed_positions  # actual position objects

    # === 2. Compute statistics ===
    statistics = Statistics(trading_state, config.main_time_series.candle_size)
    metrics = statistics.to_dict()  # dict containing all performance metrics

    # === Prepare chart data arrays ===
    chart_labels = []
    pnl_data = []
    run_up_data = []
    drawdown_data = []
    cumulative_pnl_data = []

    for pos in closed_positions:
        pos_dict = pos.to_dict()
        close_dt = pos_dict['close_datetime']
        label = close_dt.strftime("%Y-%m-%d") if not isinstance(close_dt, str) else close_dt.split("T")[0]
        
        chart_labels.append(label)
        pnl_data.append(pos_dict.get("profit_and_loss", 0))
        run_up_data.append(pos_dict.get("run_up", 0))
        drawdown_data.append(pos_dict.get("drawdown", 0))
        cumulative_pnl_data.append(pos_dict.get("cumulative_profit_and_loss", 0))

    # # Get the time_series that matches the main_time_series declaration
    # print(config.main_time_series)
    # chart_time_series = next(
    #     (ts for ts in config.time_series if ts.candle_size_str == config.main_time_series),
    #     None
    # )

    candle_data = [
    {
        "time": row["Datetime"],   # Or %Y-%m-%dT%H:%M:%S if intraday
        "open": float(row["Open"]),
        "high": float(row["High"]),
        "low": float(row["Low"]),
        "close": float(row["Close"]),
    }
        for _, row in config.main_time_series.df.iterrows()
    ]   

    # === 3. Render HTML partials ===
    trade_analysis_html = render_template(
        "partials/trade_analysis.html",
        metrics=metrics
    )

    list_of_trades_html = render_template(
        "partials/list_of_trades.html",
        positions=closed_positions
    )

    overview_html = render_template(
        "partials/overview.html",
        metrics=metrics
    )

    chart_html = render_template(
        "partials/chart.html",
        candles=candle_data
    )


    # === 4. Return JSON payload including chart data ===
    return jsonify({
        "trade_analysis": trade_analysis_html,
        "list_of_trades": list_of_trades_html,
        "overview": overview_html,     
        "chartLabels": chart_labels,
        "pnlData": pnl_data,
        "runUpData": run_up_data,
        "drawdownData": drawdown_data,
        "cumulativePnLData": cumulative_pnl_data,
        "metrics": metrics,
        "chart": chart_html,
        "candles": candle_data
    })






    # data = request.get_json()

    # # Example: simulate the 'positions' list
    # positions = [
    #     {
    #         "close_datetime": "2025-11-01 14:00",
    #         "exit_signal": "TP1",
    #         "close_market_price": 104.25,
    #         "exit_position_size": 1.0,
    #         "profit_and_loss": 250.0,
    #         "profit_and_loss_percent": 5.0,
    #         "run_up": 300.0,
    #         "run_up_pct": 6.0,
    #         "drawdown": -100.0,
    #         "drawdown_pct": -2.0,
    #         "cumulative_profit_and_loss": 250.0,
    #         "open_datetime": "2025-10-30 09:00",
    #         "entry_signal": "Long",
    #         "open_market_price": 100.00,
    #         "quantity": 1.0
    #     }
    # ]

    # # Render the "List of Trades" HTML server-side
    # list_of_trades_html = render_template('partials/list_of_trades.html', positions=positions)

    # # Example placeholders for other tabs:
    # return jsonify({
    #     "overview": "<h3>Overview</h3><p>Summary of strategy performance.</p>",
    #     "performance": "<h3>Performance</h3><p>Profit factor: 1.8</p>",
    #     "trade_analysis": "<h3>Trade Analysis</h3><p>Sharpe ratio: 1.5</p>",
    #     "list_of_trades": list_of_trades_html
    # })


if __name__ == '__main__':
    app.run(debug=True)
