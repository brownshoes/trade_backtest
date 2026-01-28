
# The empty [] is REQUIRED
IDENTIFY_ENTRY_CLASSES = {
    "SupertrendEntry": [],
    "SupertrendMAEntry": [],
    "MACDEntry": [],
    "RSIEntry": []
}

IDENTIFY_EXIT_CLASSES = {
    "SupertrendExit": [],
    "SupertrendMAExit": [],
    "MACDExit": [],
    "RSIExit": []
}

ENTRY_TRADE_CONDITIONS_CLASSES = {
    "NoEntryCondition": [],
    "OnlyOneOpenBuyCondition": [],
    "OnlyOneOpenPositionEntryCondition": [],
    "MustBeWithinPercentEntryCondition": ["percent_range"],
}

EXIT_TRADE_CONDITIONS_CLASSES = {
    "NoExitCondition": [],
    "ExitOnPercentIncrease":  ["percent_increase"],
    "ExitOnPercentDecrease": ["percent_decrease"],
    "ExitOnPercentIncreaseAndPositionIsUnsold": ["percent_increase"],
    "ExitOnPercentDecrease": ["percent_decrease"],
    "ExitOnPercentIncreaseAndPositionIsUnsold": ["percent_increase"],

    "ExitOnIncreaseOrDecrease": ["percent_decrease", "percent_increase"],
    "ExitIfBelowPrice": ["exit_price"],
    "ExitAfterPeriodOfTime": ["time_period"]
}

BUY_STRATEGIES_CLASSES = {
    "LimitBuyPercentEquity": ["percent_equity", "percent_below_current_price"]
}

SELL_STRATEGIES_CLASSES = {
    "MarketSell": []
}

EXIT_STRATEGIES_CLASSES = {
    "LimitExitPercentAbove": ["percent_above_current_price"]
}