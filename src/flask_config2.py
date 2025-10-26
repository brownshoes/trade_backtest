from flask import Flask, render_template, request, jsonify
import json

from indicators.indicator_classes import INDICATOR_CLASSES
from customization.customization_classes import IDENTIFY_ENTRY_CLASSES, IDENTIFY_EXIT_CLASSES, ENTRY_TRADE_CONDITIONS_CLASSES,EXIT_TRADE_CONDITIONS_CLASSES,BUY_STRATEGIES_CLASSES, SELL_STRATEGIES_CLASSES, EXIT_STRATEGIES_CLASSES

from init.initalization import backtest_init
from configs.create_config import create_config_from_json

from log.logger import setup_logger
log = setup_logger("Flask", mode="off")

app = Flask(__name__)

@app.route("/")
def index():
    return render_template(
        "config_form2.html",
        indicators=INDICATOR_CLASSES,
        identify_entry_classes=IDENTIFY_ENTRY_CLASSES,
        identify_exit_classes=IDENTIFY_EXIT_CLASSES,
        entry_trade_conditions_classes=ENTRY_TRADE_CONDITIONS_CLASSES,
        exit_trade_conditions_classes=EXIT_TRADE_CONDITIONS_CLASSES,
        buy_strategies_classes=BUY_STRATEGIES_CLASSES,
        sell_strategies_classes=SELL_STRATEGIES_CLASSES,
        exit_strategies_classes=EXIT_STRATEGIES_CLASSES
    )


@app.route("/submit", methods=["POST"])
def submit():
    json_data = request.get_json()
    print("📦 Received data:\n", json.dumps(json_data, indent=4))

    config = create_config_from_json(json_data)
    backtest_init(config)


    # Do whatever you want with the indicators here (save, process, etc.)
    return jsonify({"status": "success", "received": json_data})

if __name__ == "__main__":
    app.run(debug=True)
