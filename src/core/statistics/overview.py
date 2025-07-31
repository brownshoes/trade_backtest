class Overview:
    def __init__(self):
        self.dataframe = None # trade number to price and trade number to actual win/loss


        
        self.totalPL = None 
        self.max_equity_drawdown = None
        self.total_trades = None
        self.profitable_trades_percent = None
        self.profitable_trades = None 
        self.profit_factor = None


    def on_iteration(self):
        pass



    def on_completion(self):

