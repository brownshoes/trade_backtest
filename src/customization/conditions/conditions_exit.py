from decimal import Decimal

from utils.calc import percent_change

import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)

'''Default that never exits based on the condition of an open_position'''
class NoExitCondition:
    def conditions_met_exit(self, trading_state, exg_state, open_position) -> bool:
        return False


'''Exit if an open position increases by a certain percent'''
class ExitOnPercentIncrease:
    def __init__(self, percent_increase: float = 1.5):
        self.percent_increase = percent_increase

    def conditions_met_exit(self, trading_state, exg_state, open_position) -> bool:
        percent_diff  = percent_change(exg_state.current_price, open_position.entry_price)
        return percent_diff  >= self.percent_increase


'''Exit if an open position decreases by a certain percent'''
class ExitOnPercentDecrease:
    def __init__(self, percent_decrease: float = 3):
        self.percent_decrease = percent_decrease
        logger.info(f"ExitOnPercentDecrease set to exit on a {self.percent_decrease}% decrease")

    def conditions_met_exit(self, trading_state, exg_state, open_position) -> bool:
        change = percent_change(exg_state.current_price, open_position.entry_price)
        if change <= -self.percent_decrease:
            logger.info(f"ExitOnPercentDecrease triggered: {change}")
            return True
        return False
    
'''
Exit if an open position has not been sold and increases by a certain percent.
To be used to sell a portion of the position if percentage increase if met
'''
class ExitOnPercentIncreaseAndPositionIsUnsold:
    '''
    Exit if an open position has not been sold and increases by a certain percent.
    To be used to sell a portion of the position if percentage increase is met.
    '''
    def __init__(self, percent_increase: float = 1.0):
        self.percent_increase = percent_increase
        self.exit_on_percent_increase = ExitOnPercentIncrease(self.percent_increase)

    def conditions_met_exit(self, trading_state, exg_state, open_position) -> bool:
        if open_position.times_sold == 0 and self.exit_on_percent_increase.conditions_met_exit(trading_state, exg_state, open_position):
            return True
        return False


'''Exit if percent rises or falls above or below a certain percent'''
class ExitOnIncreaseOrDecrease:
    def __init__(self, percent_decrease: float = 10, percent_increase: float = 1.5):
        self.percent_decrease = percent_decrease
        self.percent_increase = percent_increase

        self.exit_on_percent_decrease = ExitOnPercentDecrease(self.percent_decrease)
        self.exit_on_percent_increase = ExitOnPercentIncrease(self.percent_increase)

    def conditions_met_exit(self, trading_state, exg_state, open_position) -> bool:
        increase = self.exit_on_percent_increase.conditions_met_exit(trading_state, exg_state, open_position)
        decrease = self.exit_on_percent_decrease.conditions_met_exit(trading_state, exg_state, open_position)
        return increase or decrease
    
'''Exit if the market price goes below a value'''
class ExitIfBelowPrice:
    def __init__(self, exit_price):
        self.exit_price = Decimal(exit_price)

    def conditions_met_exit(self, trading_state, exg_state, open_position) -> bool:
        if exg_state.current_price < self.exit_price:
            logger.info(f"Price below ${self.exit_price} - Condition exit met")
            return True
        return False

'''Exit after a period of time has passed in minutes. For Testing'''
class ExitAfterPeriodOfTime:
    def __init__(self, time_period: int = 3):
        self.time_period = time_period

    def conditions_met_exit(self, trading_state, exg_state, open_position) -> bool:
        elapsed_seconds = exg_state.current_timestamp - open_position.buy_info.order.execution_timestamp
        print(f"ExitAfterPeriodOfTime Time passed: {elapsed_seconds} seconds")
        
        if elapsed_seconds >= self.time_period * 60:
            return True
        return False