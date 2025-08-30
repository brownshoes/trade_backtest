from init.config import Config
from indicators.supertrend import Supertrend
from customization.identify.entry.supertrend import SupertrendEntry
from customization.identify.exit.supertrend import SupertrendExit
from customization.conditions.exit_trade_conditions import ExitOnPercentDecrease
from customization.buy_sell_strategies.buy_strategies import LimitBuyPercentEquity
from customization.buy_sell_strategies.sell_strategies import MarketSell
from customization.buy_sell_strategies.exit_strategies import LimitExitPercentAbove

# Indicators
supertrend = Supertrend("15m")

default_config = Config(
    # === Identifiers ===
    name = "Default Config",            # Name of the config
    
    # === Execution Settings ===
    mode="BACKTEST",                    # Operation mode: BACKTEST, LIVE, or PAPER
    trade=True,                         # If True, trading actions are executed

    # === Backtest Time Range ===
    start_time="2024-01-01 00:00",      # Start datetime of the backtest period
    end_time="2024-10-01 00:00",        # End datetime of the backtest period

    # === Initial Portfolio Holdings ===
    USD_holdings=10000.0,              # Starting USD capital
    coin_holdings=1.5,                 # Starting coin (crypto) amount

    # === Trading Fees ===
    maker_fee=0.001,                   # Maker order fee (usually lower)
    taker_fee=0.002,                   # Taker order fee (usually higher)

    # === Timeframe Configuration ===
    time_series=['15m', '1h'],         # Timeframes used for indicators/data
    main_time_series="15m",            # Primary timeframe for strategy logic
    exit_time_series=['15m', '1h'],    # Timeframes used for exit logic

    # === Indicators ===
    indicators=[supertrend],           # List of technical indicators used

    # === Entry and Exit Signal Logic ===
    identify_entry=[SupertrendEntry(supertrend)],  # Signal logic for entering trades
    identify_exit=[SupertrendExit(supertrend)],    # Signal logic for exiting trades

    # === Trade Filters / Conditions ===
    entry_trade_conditions=[],                         # Conditions to allow entry
    exit_trade_conditions=[ExitOnPercentDecrease()],   # Conditions to trigger an exit

    # === Order Execution Strategies ===
    buy_strategy=LimitBuyPercentEquity(),          # Defines how buy orders are placed
    sell_strategy=MarketSell(),                    # Defines how sell orders are placed
    exit_strategy=LimitExitPercentAbove(),          # Defines how exits are executed

    # === Order Execution Strategies ===
    csv_input_file = 'csv\csv_backtest\short_btc.csv'
)