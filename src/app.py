import traceback
from flask import Flask, render_template, request, jsonify, render_template_string
import json
import os

import pandas as pd

from indicators.indicator_classes import INDICATOR_CLASSES
from customization.customization_classes import IDENTIFY_ENTRY_CLASSES, IDENTIFY_EXIT_CLASSES, ENTRY_TRADE_CONDITIONS_CLASSES,EXIT_TRADE_CONDITIONS_CLASSES,BUY_STRATEGIES_CLASSES, SELL_STRATEGIES_CLASSES, EXIT_STRATEGIES_CLASSES

from init.initalization import backtest_init
from configs.create_config import create_config_from_json
from core.position_tracking.statistics import Statistics

from database.db_config_results_model import ConfigResult
from database.db_config_results_access import create_entry, get_all_entries

from log.logger import setup_logger
log = setup_logger("Flask", mode="Off")

# Create DB and tables on startup
from database.db_setup import init_db
init_db()

app = Flask(__name__)

LAST_BACKTEST_RESULT = None


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

@app.route("/config-results", methods=["GET"])
def fetch_config_results():
    log.critical("fetch_config_results")
    try:
        rows = get_all_entries()  # returns list of ConfigResult objects

        # Convert each row to a dict for JSON
        results = [row.to_json() if isinstance(row.to_json(), dict) else row.to_json() for row in rows]

        # If to_json() returns JSON string, parse it
        import json
        for i, r in enumerate(results):
            if isinstance(r, str):
                results[i] = json.loads(r)

        return jsonify(results), 200

    except Exception as e:
        app.logger.error("Failed to fetch config results: %s", e)
        return jsonify({"error": "Failed to fetch results"}), 500

@app.route("/save", methods=["POST"])
def save():
    if LAST_BACKTEST_RESULT is None:
        return jsonify({
            "error": "No backtest result available. Call /submit first."
        }), 400

    try:
        result = LAST_BACKTEST_RESULT

        config = result["config"]
        json_data = result["json_data"]
        metrics = result["metrics"]

        #=== Save to Directory ===
        # Ensure directory exists
        save_dir = "configs"
        os.makedirs(save_dir, exist_ok=True)

        # Save JSON file
        json_file_path = os.path.join(save_dir, f"{config.name}.json")
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)

        log.info("Saved JSON data to disk: %s", json_file_path)

        #=== Save to Database ===
        config_result = ConfigResult(
            json_file_name=config.name,
            start_time=config.start_time,
            end_time=config.end_time,

            total_pnl=float(metrics["total_profit_and_loss"]),
            total_pnl_percent=float(metrics["total_profit_and_loss_percent"]),
            max_drawdown=float(metrics["max_equity_drawdown"]),
            total_trades=int(metrics["total_trades"]),
            profit_factor=float(metrics["profit_factor"]),
            percent_profitable=float(metrics["percent_profitable"]),
        )

        log.info("Saving backtest result to database: %s", config.name)

        success, error_msg = create_entry(config_result)

        if not success:
            return jsonify({
                "status": "error",
                "message": error_msg
            }), 409


        return jsonify({
            "status": "saved",
            "json_file_name": config.name
        }), 200

    except Exception as e:
        log.error("Error in save route", exc_info=True)
        return jsonify({
            "error": str(e)
        }), 500

@app.route("/submit", methods=["POST"])
def submit():
    global LAST_BACKTEST_RESULT

    try:
        json_data = request.get_json()
        log.info(f"📦 Received data:\n{json.dumps(json_data, indent=4)}")

        # === 1. Build and run backtest ===
        config = create_config_from_json(json_data)
        log.info(config)
        backtest_init(config)

        trading_state = config.trading_state
        closed_positions = trading_state.closed_positions

        # === 2. Compute statistics ===
        statistics = Statistics(trading_state, config.main_time_series.candle_size)
        metrics = statistics.to_dict()

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

        # === 3. Store everything globally ===
        LAST_BACKTEST_RESULT = {
            "config": config,
            "json_data": json_data,     
            "metrics": metrics,
            "chart_data": {
                "labels": chart_labels,
                "pnl": pnl_data,
                "run_up": run_up_data,
                "drawdown": drawdown_data,
                "cumulative_pnl": cumulative_pnl_data,
            },
            "closed_positions": closed_positions,
        }

        # === 4. Store everything globally ===
        candle_data = _format_candle_data(config.main_time_series.df)
        trade_markers = _build_trade_markers(closed_positions)
        plotting = _format_plotting(config.indicators)

        # === 5. Render HTML partials ===
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

        # === 6. Return JSON payload including chart data ===
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
            "candles": candle_data,
            "tradeMarkers": trade_markers,
            "indicators": plotting,
        })
    
    except Exception as e:
        log.error(f"Error in submit route: {str(e)}", exc_info=True)
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
    

def _format_candle_data(df):
    # Format candle data for TradingView Lightweight Charts
    candle_data = []
    for idx, row in df.iterrows():
        timestamp = row["Timestamp"]
        open_val = row["Open"]
        high_val = row["High"]
        low_val = row["Low"]
        close_val = row["Close"]
        
        # Skip rows with null/NaN values
        if any(pd.isna(x) for x in [timestamp, open_val, high_val, low_val, close_val]):
            continue
        
        try:
            candle_data.append({
                "time": int(timestamp),
                "open": float(open_val),
                "high": float(high_val),
                "low": float(low_val),
                "close": float(close_val),
            })
        except Exception as e:
            log.warning(f"Error processing row {idx}: {e}")
            continue

    log.info(f"Generated {len(candle_data)} valid candles for chart")

    return candle_data

def _build_trade_markers(closed_positions):
    # === Prepare trade markers (entry and exit points) ===
    trade_markers = []
    for pos in closed_positions:
        # Entry marker
        entry_timestamp = int(pos.open_timestamp)
        entry_price = pos.open_market_price
        
        trade_markers.append({
            "time": entry_timestamp,
            "position": "belowBar",
            "color": "#2196F3",
            "shape": "arrowUp",
            "text": f"Entry @ {entry_price:.2f}"
        })
        
        # Exit marker
        exit_timestamp = int(pos.close_timestamp)
        exit_price = pos.close_market_price
        pnl = pos.profit_and_loss
        
        # Color based on profit/loss
        color = "#4CAF50" if pnl > 0 else "#F44336"
        
        trade_markers.append({
            "time": exit_timestamp,
            "position": "aboveBar",
            "color": color,
            "shape": "arrowDown",
            "text": f"Exit @ {exit_price:.2f} (PnL: {pnl:.2f})"
        })

    log.info(f"Generated {len(trade_markers)} trade markers")

    return trade_markers

def _format_plotting(indicators):
    plotting = []

    for indicator in indicators:
        indicator_plots = indicator.plotting()
        if not indicator_plots:
            continue

        for plot in indicator_plots:
            df = plot["data"]

            timestamps = []
            values = []

            for idx, row in df.iterrows():
                try:
                    timestamps.append(int(row["Timestamp"]))
                    # IMPORTANT: preserve None for JS null handling
                    val = row["values"]
                    values.append(None if pd.isna(val) else float(val))
                except Exception as e:
                    log.warning(f"Error processing row {idx}: {e}")
                    continue

            new_plot = plot.copy()
            new_plot["data"] = {
                "Timestamp": timestamps,
                "values": values
            }

            plotting.append(new_plot)
    return plotting

if __name__ == '__main__':
    app.run(debug=True)
