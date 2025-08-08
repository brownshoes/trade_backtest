from utils.calc import percent_change

'''An Entry condition is a condition that is dependant on the overall state or trading state to allow a buy'''

'''Default buy. No stipulations on executing a buy'''
class NoEntryCondition:
    def trade_conditions_met_for_entry(self, trading_state, exg_state):
        return True

'''Only allows one buy attempt at a time. If there is an already open buy/ a buy identified, then it doesn't allow a second buy'''
class OnlyOneOpenBuyCondition:
    def trade_conditions_met_for_entry(self, trading_state, exg_state):
        return len(trading_state.open_buy_orders) == 0

'''Only allows one open position at a time. If there is an already an open position then a buy is not allowed until it is sold.'''
class OnlyOneOpenPositionEntryCondition:
    def trade_conditions_met_for_entry(self, trading_state, exg_state):
        return len(trading_state.open_positions) == 0

'''Ensures that multiple positions aren't opened at the same price range. Allows entry if the current price is a percentage outside a current open position's buy price.'''
class MustBeWithinPercentEntryCondition:
    def __init__(self, percent_range: float = 1.5):
        self.percent_range = percent_range

    def trade_conditions_met_for_entry(self, trading_state, exg_state):
        if not trading_state.open_positions:
            return True

        for position in trading_state.open_positions.values():
            percent_diff  = abs(percent_change(exg_state.current_price, position.entry_price))
            if percent_diff  < self.percent_range:
                return False

        return True