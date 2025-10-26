from init.config import Config
from decimal import Decimal
import json

# === Indicators ===
from indicators.simple_moving_average import SimpleMovingAverage
from indicators.supertrend import Supertrend

# === Identify Entry ===
from customization.identify.entry.supertrend_ma import SupertrendMAEntry
from customization.identify.entry.supertrend import SupertrendEntry
from customization.identify.entry.time_interval import TimeIntervalEntry

# === Identify Exit ===
from customization.identify.exit.supertrend_ma import SupertrendMAIdentifyExit
from customization.identify.exit.supertrend import SupertrendExit

# === Entry Conditions ===
from customization.conditions.entry_trade_conditions import NoEntryCondition, OnlyOneOpenBuyCondition, OnlyOneOpenPositionEntryCondition, MustBeWithinPercentEntryCondition

# === Exit Conditions ===
from customization.conditions.exit_trade_conditions import NoExitCondition, ExitOnPercentIncrease, ExitOnPercentDecrease, ExitOnPercentIncreaseAndPositionIsUnsold, ExitOnIncreaseOrDecrease, ExitIfBelowPrice, ExitAfterPeriodOfTime

# === Buy Strategies ===
from customization.buy_sell_strategies.buy_strategies import LimitBuyPercentEquity

# === Sell Strategies ===
from customization.buy_sell_strategies.sell_strategies import MarketSell

# === Exit Strategies ===
from customization.buy_sell_strategies.exit_strategies import LimitExitPercentAbove

# Class lookup dictionary
CLASS_MAP = {
    # === Indicators ===
    "Supertrend": Supertrend,
    "SimpleMovingAverage": SimpleMovingAverage,

    # === Identify Entry ===
    "SupertrendEntry": SupertrendEntry,
    "SupertrendMAEntry": SupertrendMAEntry,
    "TimeIntervalEntry": TimeIntervalEntry,

    # === Identify Exit ===
    "SupertrendExit": SupertrendExit,
    "SupertrendMAIdentifyExit": SupertrendMAIdentifyExit,

    # === Entry Conditions ===
    "NoEntryCondition": NoEntryCondition,
    "OnlyOneOpenBuyCondition": OnlyOneOpenBuyCondition,
    "OnlyOneOpenPositionEntryCondition": OnlyOneOpenPositionEntryCondition,
    "MustBeWithinPercentEntryCondition": MustBeWithinPercentEntryCondition,

    # === Exit Conditions ===
    "NoExitCondition": NoExitCondition,
    "ExitOnPercentIncrease": ExitOnPercentIncrease,
    "ExitOnPercentDecrease": ExitOnPercentDecrease,
    "ExitOnPercentIncreaseAndPositionIsUnsold": ExitOnPercentIncreaseAndPositionIsUnsold,
    "ExitOnIncreaseOrDecrease": ExitOnIncreaseOrDecrease,
    "ExitIfBelowPrice": ExitIfBelowPrice,
    "ExitAfterPeriodOfTime": ExitAfterPeriodOfTime,

    # === Buy Strategies ===
    "LimitBuyPercentEquity": LimitBuyPercentEquity,

    # === Sell Strategies ===
    "MarketSell": MarketSell,

    # === Exit Strategies ===
    "LimitExitPercentAbove": LimitExitPercentAbove,
}

def serialize_obj(obj, indicator_map=None):
    from core.time_series import TimeSeries
    from core.series import Series

    if obj is None:
        return None
    
    # Convert Decimal to float
    if isinstance(obj, Decimal):
        return float(obj)

    # TimeSeries → use candle_size_str
    if isinstance(obj, TimeSeries):
        return obj.candle_size_str

    # Series → ignore
    if isinstance(obj, Series):
        return None

    cls_name = obj.__class__.__name__

    # Entry/Exit Signal that references an indicator → use index
    # --- Handle indicator references (entry/exit) ---
    if indicator_map and hasattr(obj, '__dict__'):
        matched_refs = [
            ref_id
            for ind_obj, ref_id in indicator_map.items()
            if ind_obj in obj.__dict__.values()
        ]
        if matched_refs:
            return {
                "type": cls_name,
                "indicator_ref": matched_refs  # always a list
            }


    # Simple types
    if isinstance(obj, (str, int, float, bool, list, dict)):
        return obj

    # General object with serializable args
    if hasattr(obj, "__dict__"):
        args = []
        for val in obj.__dict__.values():

            if isinstance(val, Series):
                continue
            elif isinstance(val, TimeSeries):
                args.append(val.candle_size_str)
            # Convert Decimal to float
            elif isinstance(val, Decimal):
                return args.append(float(val))
            else:
                args.append(val)
        block = {
            "type": cls_name,
            "args": args
        }       

        if indicator_map and obj in indicator_map:
            block["ref"] = indicator_map[obj]
        return block
    # Fallback
    return {"type": cls_name}




def config_to_json(config):
    indicators = config.indicators

    indicator_map = {ind: i + 1 for i, ind in enumerate(indicators)}

    return {
        "name": config.name,
        "mode": config.mode,
        "trade": config.trade,
        "start_time": config.start_time,
        "end_time": config.end_time,
        "USD_holdings": config.USD_holdings,
        "coin_holdings": config.coin_holdings,
        "maker_fee": config.maker_fee,
        "taker_fee": config.taker_fee,

        "time_series": [ts.candle_size_str for ts in config.time_series],
        "main_time_series": config.main_time_series.candle_size_str,
        "exit_time_series": [ts.candle_size_str for ts in config.exit_time_series],

        "indicators": [serialize_obj(ind, indicator_map) for ind in indicators],

        "identify_entry": [serialize_obj(entry, indicator_map) for entry in config.identify_entry],
        "identify_exit": [serialize_obj(exit, indicator_map) for exit in config.identify_exit],

        "entry_trade_conditions": [serialize_obj(cond) for cond in config.entry_trade_conditions],
        "exit_trade_conditions": [serialize_obj(cond) for cond in config.exit_trade_conditions],

        "buy_strategy": serialize_obj(config.buy_strategy),
        "sell_strategy": serialize_obj(config.sell_strategy),
        "exit_strategy": serialize_obj(config.exit_strategy),

        "csv_input_file": config.csv_input_file
    }


def deserialize_obj(obj_def, indicator_ref_map=None):
    if obj_def is None:
        return None

    cls = CLASS_MAP[obj_def["type"]]

    if indicator_ref_map is not None and "indicator_ref" in obj_def:
        resolved_objects = [indicator_ref_map[idx] for idx in obj_def["indicator_ref"]]
        return cls(*resolved_objects)

    if "args" in obj_def:
        return cls(*obj_def["args"])

    return cls()


def create_config_from_json(json_data):
    indicators = [deserialize_obj(ind) for ind in json_data["indicators"]]

    indicator_ref_map = {ind["ref"]: obj for ind, obj in zip(json_data["indicators"], indicators)}

    identify_entry = [deserialize_obj(obj, indicator_ref_map) for obj in json_data["identify_entry"]]
    identify_exit = [deserialize_obj(obj, indicator_ref_map) for obj in json_data["identify_exit"]]
    entry_conditions = [deserialize_obj(obj) for obj in json_data.get("entry_trade_conditions", [])]
    exit_conditions = [deserialize_obj(obj) for obj in json_data.get("exit_trade_conditions", [])]

    buy_strategy = deserialize_obj(json_data["buy_strategy"])
    sell_strategy = deserialize_obj(json_data["sell_strategy"])
    exit_strategy = deserialize_obj(json_data["exit_strategy"])

    return Config(
        name=json_data["name"],
        mode=json_data["mode"],
        trade=json_data["trade"],
        start_time=json_data["start_time"],
        end_time=json_data["end_time"],
        USD_holdings=json_data["USD_holdings"],
        coin_holdings=json_data["coin_holdings"],
        maker_fee=json_data["maker_fee"],
        taker_fee=json_data["taker_fee"],
        time_series=json_data["time_series"],
        main_time_series=json_data["main_time_series"],
        exit_time_series=json_data["exit_time_series"],
        indicators=indicators,
        identify_entry=identify_entry,
        identify_exit=identify_exit,
        entry_trade_conditions=entry_conditions,
        exit_trade_conditions=exit_conditions,
        buy_strategy=buy_strategy,
        sell_strategy=sell_strategy,
        exit_strategy=exit_strategy,
        csv_input_file=json_data["csv_input_file"]
    )


# Optional helpers

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that converts Decimal → float."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def save_config_to_file(config, filepath):
    json_data = config_to_json(config)
    with open(filepath, 'w') as f:
        json.dump(json_data, f, indent=2, cls=DecimalEncoder)


def load_config_from_file(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    return create_config_from_json(data)
