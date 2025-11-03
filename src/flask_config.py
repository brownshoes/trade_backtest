from flask import Flask, render_template, request, redirect, url_for, jsonify
import json

from init.flask_init import DEFAULT_CONFIG
from indicators.indicator_classes import INDICATOR_CLASSES
from customization.customization_classes import IDENTIFY_ENTRY_CLASSES, IDENTIFY_EXIT_CLASSES, ENTRY_TRADE_CONDITIONS_CLASSES,EXIT_TRADE_CONDITIONS_CLASSES,BUY_STRATEGIES_CLASSES, SELL_STRATEGIES_CLASSES, EXIT_STRATEGIES_CLASSES

from log.logger import setup_logger
log = setup_logger("Flask", mode="off")

app = Flask(__name__)

#config_data = DEFAULT_CONFIG.to_json()

@app.route("/save-config", methods=["POST"])
def save_config():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No JSON received"}), 400

    # Save to file
    with open('config.json', "w") as f:
        json.dump(data, f, indent=4)

    # Print to console
    print("Received config JSON:")
    print(json.dumps(data, indent=4))

    return jsonify({"status": "success", "message": "Config saved!"})


@app.route('/', methods=['GET', 'POST'])
def config():
    #global config_data
    config_data = {}

    if request.method == 'POST':
        # Update the config_data with the submitted form data
        config_data['name'] = request.form['name']
        config_data['mode'] = request.form['mode']
        config_data['trade'] = 'trade' in request.form
        config_data['start_time'] = request.form['start_time']
        config_data['end_time'] = request.form['end_time']
        config_data['USD_holdings'] = float(request.form['USD_holdings'])
        config_data['coin_holdings'] = float(request.form['coin_holdings'])
        config_data['maker_fee'] = float(request.form['maker_fee'])
        config_data['taker_fee'] = float(request.form['taker_fee'])
        config_data['main_time_series'] = request.form['main_time_series']
        config_data['csv_input_file'] = request.form['csv_input_file']

        # Time series lists
        config_data['time_series'] = [
            value for key, value in request.form.items() if key.startswith('time-series-')
        ]
        config_data['exit_time_series'] = [
            value for key, value in request.form.items() if key.startswith('exit-time-series-')
        ]

        # --- Indicators ---
        config_data['indicators'] = parse_indicators(request.form)

        # --- Identify entry/exit ---
        config_data['identify_entry'] = parse_identify_rules(request.form, "identify_entry")
        config_data['identify_exit'] = parse_identify_rules(request.form, "identify_exit")

         # --- Trade conditions ---
        config_data['entry_trade_conditions'] = parse_trade_conditions(request.form, 'entry-trade-condition')
        config_data['exit_trade_conditions'] = parse_trade_conditions(request.form, 'exit-trade-condition')

        # --- Strategies ---
        config_data['buy_strategy'] = parse_strategy(request.form, 'buy-strategy')
        config_data['sell_strategy'] = parse_strategy(request.form, 'sell-strategy')
        config_data['exit_strategy'] = parse_strategy(request.form, 'exit-strategy')





        


        # Optional: Save to file
        with open('config.json', 'w') as f:
            json.dump(config_data, f, indent=2)

        return redirect(url_for('config'))

    return render_template(
        'config_form.html',
        indicator_classes=INDICATOR_CLASSES,
        identify_entry_classes=IDENTIFY_ENTRY_CLASSES,
        identify_exit_classes=IDENTIFY_EXIT_CLASSES,
        entry_condition_classes=ENTRY_TRADE_CONDITIONS_CLASSES,
        exit_condition_classes=EXIT_TRADE_CONDITIONS_CLASSES,
        buy_strategy_classes=BUY_STRATEGIES_CLASSES,
        sell_strategy_classes=SELL_STRATEGIES_CLASSES,
        exit_strategy_classes=EXIT_STRATEGIES_CLASSES
    )


# ==================== Trade Conditions ====================
def parse_trade_conditions(form_data, prefix):
    conditions = []
    num_items = int(form_data.get(f'num_{prefix}s', 0))

    for i in range(num_items):
        condition_type = form_data.get(f'{prefix}_type_{i}')
        args = {}
        for key, value in form_data.items():
            if key.startswith(f'{prefix}_arg_{i}_'):
                arg_name = key.replace(f'{prefix}_arg_{i}_', '')
                args[arg_name] = float(value) if value.replace('.', '', 1).isdigit() else value

        if condition_type:
            conditions.append({
                "type": condition_type,
                "args": args
            })
    return conditions

# ==================== Strategies ====================
def parse_strategy(form_data, prefix):
    # Only parse if the strategy exists
    if not form_data.get(f'has_{prefix}', '0') == '1':
        return None

    strategy_type = form_data.get(f'{prefix}_type_0')
    args = {}
    for key, value in form_data.items():
        if key.startswith(f'{prefix}_arg_0_'):
            arg_name = key.replace(f'{prefix}_arg_0_', '')
            args[arg_name] = float(value) if value.replace('.', '', 1).isdigit() else value

    return {"type": strategy_type, "args": args}


def parse_indicators(form_data):
    indicators = []
    num_indicators = int(form_data.get('num_indicators', 0))

    for i in range(num_indicators):
        ind_type = form_data.get(f'indicator_type_{i}')
        if not ind_type:
            continue

        args = []
        for key, value in form_data.items():
            if key.startswith(f'indicator_arg_{i}_') and value:
                args.append(int(value) if value.isdigit() else value)

        indicators.append({"type": ind_type, "args": args})

    return indicators


def parse_identify_rules(form_data, block_name):
    """
    Parse identify_entry or identify_exit rules from form_data.

    block_name: "identify_entry" or "identify_exit"
    """
    rules = []

    # Map block_name to exact payload key for count
    num_key_map = {
        "identify_entry": "num_identify_entries",
        "identify_exit": "num_identify_exits"
    }
    num_key = num_key_map.get(block_name)
    if not num_key:
        return rules

    num_items_raw = form_data.get(num_key, 0)
    print(f"{block_name}: {num_key} = {num_items_raw}")

    try:
        num_items = int(num_items_raw)
    except ValueError:
        num_items = 0

    for i in range(num_items):
        rule_type = form_data.get(f'{block_name}_type_{i}')
        ref_raw = form_data.get(f'{block_name}_indicator_ref_{i}')
        print(f"i={i}, rule_type={rule_type}, ref_raw={ref_raw}")

        if not rule_type or ref_raw is None:
            continue

        try:
            indicator_ref_index = int(ref_raw)
        except ValueError:
            indicator_ref_index = None

        rules.append({
            "type": rule_type,
            "indicator_ref_index": indicator_ref_index
        })

    print(f"Parsed {block_name}: {rules}")
    return rules







if __name__ == '__main__':
    app.run(debug=True)
