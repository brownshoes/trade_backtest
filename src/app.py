from flask import Flask, render_template, request, jsonify, render_template_string
import json

from indicators.indicator_classes import INDICATOR_CLASSES
from customization.customization_classes import IDENTIFY_ENTRY_CLASSES, IDENTIFY_EXIT_CLASSES, ENTRY_TRADE_CONDITIONS_CLASSES,EXIT_TRADE_CONDITIONS_CLASSES,BUY_STRATEGIES_CLASSES, SELL_STRATEGIES_CLASSES, EXIT_STRATEGIES_CLASSES

from init.initalization import backtest_init
from configs.create_config import create_config_from_json
from core.position_tracking.statistics import Statistics

from log.logger import setup_logger
log = setup_logger("Flask", mode="off")

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
    print("📦 Received data:\n", json.dumps(json_data, indent=4))

    # === 1. Build and run backtest ===
    config = create_config_from_json(json_data)
    backtest_init(config)

    trading_state = config.trading_state

    # Pass actual position objects (not dicts) so HTML can use dot notation
    closed_positions = trading_state.closed_positions

    # === 2. Compute statistics ===
    statistics = Statistics(trading_state, config.main_time_series.candle_size)
    metrics = statistics.to_dict()

    # === 3. Render HTML partials ===
    list_of_trades_html = render_template(
        "partials/list_of_trades.html",
        positions=closed_positions
    )

    # Placeholder partials (you can replace later)
    overview_html = render_template_string("""
        <h3>Overview</h3>
        <p>Total Trades: {{ metrics.total_trades if metrics.total_trades is defined else 'N/A' }}</p>
        <p>Net Profit: {{ metrics.net_profit if metrics.net_profit is defined else 'N/A' }}</p>
    """, metrics=metrics)

    performance_html = render_template_string("""
        <h3>Performance</h3>
        <p>Profit Factor: {{ metrics.profit_factor if metrics.profit_factor is defined else 'N/A' }}</p>
        <p>Max Drawdown: {{ metrics.max_drawdown if metrics.max_drawdown is defined else 'N/A' }}</p>
    """, metrics=metrics)

    trade_analysis_html = render_template_string("""
        <h3>Trade Analysis</h3>
        <p>Sharpe Ratio: {{ metrics.sharpe_ratio if metrics.sharpe_ratio is defined else 'N/A' }}</p>
        <p>Win Rate: {{ metrics.win_rate if metrics.win_rate is defined else 'N/A' }}%</p>
    """, metrics=metrics)

    # === 4. Return JSON payload ===
    return jsonify({
        "overview": overview_html,
        "performance": performance_html,
        "trade_analysis": trade_analysis_html,
        "list_of_trades": list_of_trades_html
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
