from flask import Flask, render_template, request, redirect, url_for, jsonify
import json

from init.flask_init import DEFAULT_CONFIG
from indicators.indicator_classes import INDICATOR_CLASSES
from customization.customization_classes import IDENTIFY_ENTRY_CLASSES, IDENTIFY_EXIT_CLASSES, ENTRY_TRADE_CONDITIONS_CLASSES,EXIT_TRADE_CONDITIONS_CLASSES,BUY_STRATEGIES_CLASSES, SELL_STRATEGIES_CLASSES, EXIT_STRATEGIES_CLASSES

from log.logger import setup_logger
log = setup_logger("Flask", mode="off")

app = Flask(__name__)

#config_data = DEFAULT_CONFIG.to_json()


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

        # Handle indicators
        indicators = []
        num_indicators = int(request.form['num_indicators'])
        for i in range(num_indicators):
            type_ = request.form[f'indicator_type_{i}']
            args_raw = request.form.getlist(f'indicator_args_{i}')
            args = [int(arg) if arg.isdigit() else arg for arg in args_raw]
            indicators.append({"type": type_, "args": args})
        config_data['indicators'] = indicators

        # Handle identify_entry
        identify_entry = []
        num_entry_rules = int(request.form.get('num_entry_rules', 0))
        for i in range(num_entry_rules):
            rule_type = request.form.get(f'entry_type_{i}')
            indicator_idx = int(request.form.get(f'entry_indicator_index_{i}', 0))
            identify_entry.append({"type": rule_type, "indicator_ref_index": indicator_idx})
        config_data['identify_entry'] = identify_entry

        # Handle identify_exit
        identify_exit = []
        num_exit_rules = int(request.form.get('num_exit_rules', 0))
        for i in range(num_exit_rules):
            rule_type = request.form.get(f'exit_type_{i}')
            indicator_idx = int(request.form.get(f'exit_indicator_index_{i}', 0))
            identify_exit.append({"type": rule_type, "indicator_ref_index": indicator_idx})
        config_data['identify_exit'] = identify_exit

        # Handle entry_trade_conditions
        entry_trade_conditions = []
        num_entry_conditions = int(request.form.get('num_entry_conditions', 0))
        for i in range(num_entry_conditions):
            cond_type = request.form.get(f'entry_trade_condition_type_{i}')
            if cond_type:
                entry_trade_conditions.append({"type": cond_type})
        config_data['entry_trade_conditions'] = entry_trade_conditions

        # Handle exit_trade_conditions
        exit_trade_conditions = []
        num_exit_conditions = int(request.form.get('num_exit_conditions', 0))
        for i in range(num_exit_conditions):
            cond_type = request.form.get(f'exit_trade_condition_type_{i}')
            if cond_type:
                exit_trade_conditions.append({"type": cond_type})
        config_data['exit_trade_conditions'] = exit_trade_conditions

        # Buy Strategy
        buy_strategy_type = request.form.get('buy_strategy_type_0')
        buy_strategy_args = {
            k.replace(f'buy_strategy_arg_0_', ''): request.form[k]
            for k in request.form if k.startswith('buy_strategy_arg_0_')
        }
        config_data['buy_strategy'] = {'type': buy_strategy_type, **buy_strategy_args}

        # Sell Strategy
        sell_strategy_type = request.form.get('sell_strategy_type_0')
        sell_strategy_args = {
            k.replace(f'sell_strategy_arg_0_', ''): request.form[k]
            for k in request.form if k.startswith('sell_strategy_arg_0_')
        }
        config_data['sell_strategy'] = {'type': sell_strategy_type, **sell_strategy_args}

        # Exit Strategy
        exit_strategy_type = request.form.get('exit_strategy_type_0')
        exit_strategy_args = {
            k.replace(f'exit_strategy_arg_0_', ''): request.form[k]
            for k in request.form if k.startswith('exit_strategy_arg_0_')
        }
        config_data['exit_strategy'] = {'type': exit_strategy_type, **exit_strategy_args}


        


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



if __name__ == '__main__':
    app.run(debug=True)
