import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)

class Strategy:
    def __init__(self, exit_time_series, entry_trade_conditions, exit_trade_conditions, identify_entry, identify_exit):
        self.exit_time_series = exit_time_series

        self.entry_trade_conditions = entry_trade_conditions
        self.exit_trade_conditions = exit_trade_conditions

        self.identify_entry = identify_entry
        self.identify_exit = identify_exit


    '''-----------------------------------ENTER-----------------------------------'''
    '''Check for enty positions in all identify_entry's that had their time_series updated and entry conditions met'''
    def enter_position(self, trading_state, exg_state, time_series_updated_list):
        identified_entries = []
        for identify in self.identify_entry:
            if (
                identify.time_series in time_series_updated_list and
                identify.identify_entry() and
                self._trade_conditions_met_entry(trading_state, exg_state)
            ):
                identified_entries.append(identify)

        if identified_entries:
            identified_entries = identified_entries + self.entry_trade_conditions
            logger.info(f"Entry Identified: {exg_state.get_current_datetime()} {identified_entries}")

        return identified_entries
    
    '''trade conditions for ENTRY is 'AND'. All conditions must be true'''
    def _trade_conditions_met_entry(self, trading_state, exg_state):
        for condition in self.entry_trade_conditions:
            if not condition.trade_conditions_met_for_entry(trading_state, exg_state):
                return False
        return True
    
    '''-----------------------------------EXIT-----------------------------------'''
    def exit_positions(self, trading_state, exg_state, time_series_updated_list):
        ''' map of positions to exit_conditions for that position, if any'''
        positions_to_close = self._exit_from_conditions(trading_state, exg_state, time_series_updated_list)
        identified_exits = self._exit_from_identified(trading_state, exg_state, time_series_updated_list, self.identify_exit)

        '''if any exits identified, map all positions to identifed exits, plus any exit_conditions'''
        if identified_exits:
            for open_position in trading_state.open_positions.values():
                if open_position in positions_to_close:
                    positions_to_close[open_position] += identified_exits
                else:
                    positions_to_close[open_position] = identified_exits


        '''log the results'''
        for open_position, exits in positions_to_close.items():
            logger.info(
                f"Exit identified for: {open_position.trade_overview_buy.order.order_string()} {exits} {exg_state.get_current_datetime()}"
            )

        return positions_to_close
    
    '''Check for exits in all identify_exit's that had their time_series updated'''
    def _exit_from_identified(self, trading_state, exg_state, time_series_updated_list, identify_exit):
        identified_exits = []
        for identify in identify_exit:
            if identify.time_series in time_series_updated_list and identify.identify_exit():
                identified_exits.append(identify)

        return identified_exits

    '''Check for position exit based on if a set time_series was updated'''
    def _exit_from_conditions(self, trading_state, exg_state, time_series_updated_list):
        positions_to_close = {}

        '''if any of the exit_time_series are in the updated time series, check if any exit conditions are met'''
        if(len([x for x in self.exit_time_series if x in time_series_updated_list]) != 0):
            for open_position in trading_state.open_positions.values():
                '''ensure that we don't attempt to resell the position immediately after buying'''
                if int(open_position.trade_overview_buy.executed_timestamp) == int(exg_state.current_timestamp):
                    continue

                exit_conditions = self._trade_conditions_met_exit(trading_state, exg_state, open_position, self.exit_trade_conditions)
                if exit_conditions:
                    positions_to_close[open_position] = exit_conditions

        return positions_to_close

    '''EXIT on trade condition is 'OR'. If one condition is true, exit'''
    def _trade_conditions_met_exit(self, trading_state, exg_state, open_position, exit_trade_conditions):
        exit_conditions = []
        for condition in exit_trade_conditions:
            if condition.conditions_met_exit(trading_state, exg_state, open_position):
                exit_conditions.append(condition)
        return exit_conditions
