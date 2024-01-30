from datetime import date, timedelta
import decimal
import backtrader as bt

from backtrader_finam.finam_store import FinamStore  # Storage Finam
from my_config.Config_Finam import Config  # for authorization on Finam/Common


class LimitCancel(bt.Strategy):
    """
    We place a purchase order n% below the closing price
    If the request does not work for 1 bar, then we close it
    If it works, then we close the position. It doesn't matter, profit or loss
    """
    params = (  # Trading System Parameters
        ('timeframe', ''),
        ('LimitPct', 1),  # The purchase order is n% lower than the closing price
        ('ticker_info', ''),
    )

    def __init__(self):
        """Initialization of the trading system"""
        self.order = None  # Request to enter/exit a position

    def next(self):
        """The arrival of a new ticker bar"""
        for data in self.datas:  # We run through all the requested bars of all tickers
            ticker = data._name
            status = data._state  # 0 - Live data, 1 - History data, 2 - None
            _state = None
            _interval = self.p.timeframe

            if status in [0, 1]:
                if status: _state = "False - History data"
                else: _state = "True - Live data"

            print('{} / {} [{}] - Open: {}, High: {}, Low: {}, Close: {}, Volume: {} - Live: {}'.format(
                bt.num2date(data.datetime[0]),
                data._name,
                _interval,  # таймфрейм тикера
                data.open[0],
                data.high[0],
                data.low[0],
                data.close[0],
                data.volume[0],
                _state,
            ))

            if status == 0:  # LIVE mode
                if self.order and self.order.status == bt.Order.Submitted:  # If the request is not executed (sent to the broker)
                    return  # then we wait for the execution, we leave, we do not continue further

                # print(2222, self.position, len(self.position), bool(self.position), not self.position, type(self.position))

                if not self.position or (self.position and self.position.size <= 30):  # If there is no position
                    if self.order and self.order.status == bt.Order.Accepted:  # If the request is not executed (accepted by the broker)
                        print("Let's Cancel order.")
                        self.cancel(self.order)  # then we take it off
                    limit_price = self.data.close[0] * (1 - self.p.LimitPct / 100)  # n% lower than the closing price
                    print(f"Our limit price: {limit_price}")
                    # price should be div by step_price
                    limit_price = (limit_price // self.p.ticker_info["step_price"]) * self.p.ticker_info["step_price"]
                    limit_price = decimal.Decimal(limit_price)
                    print(f"Our limit price OK: {limit_price}")
                    self.order = self.buy(exectype=bt.Order.Limit, price=limit_price, use_credit=True)  # Limit purchase request
                    print("Order was submitted.")
                else:  # If there is a position
                    self.order = self.close()  # close a position at the market price
                    print("Order was closed.")

    def notify_trade(self, trade):
        """Changing the position status"""
        if trade.isclosed:  # If the position is closed
            self.log(f'Profit on a closed position {trade.getdataname()} Total={trade.pnl:.2f}, No Commission={trade.pnlcomm:.2f}')

    def log(self, txt, dt=None):
        """Output a date string to the console"""
        dt = bt.num2date(self.datas[0].datetime[0]) if not dt else dt  # The set date or the date of the current bar
        print(f'{dt.strftime("%d.%m.%Y %H:%M")}, {txt}')  # Output the date and time with the specified text to the console

    def notify_order(self, order):
        """Changing the status of the order"""
        if order.status in (bt.Order.Created, bt.Order.Submitted, bt.Order.Accepted):  # If the order is created, sent to the broker, accepted by the broker (not executed)
            self.log(f'Alive Status: {order.getstatusname()}. TransId={order.ref}')
        elif order.status in (bt.Order.Canceled, bt.Order.Margin, bt.Order.Rejected, bt.Order.Expired):  # If the order is canceled, there are no funds, the order is rejected by the broker, withdrawn on time (withdrawn)
            self.log(f'Cancel Status: {order.getstatusname()}. TransId={order.ref}')
        elif order.status == bt.Order.Partial:  # If the order is partially executed
            self.log(f'Part Status: {order.getstatusname()}. TransId={order.ref}')
        elif order.status == bt.Order.Completed:  # If the request is fully executed
            if order.isbuy():  # Purchase request
                self.log(f'Bought @{order.executed.price:.2f}, Cost={order.executed.value:.2f}, Comm={order.executed.comm:.2f}')
            elif order.issell():  # Order for sale
                self.log(f'Sold @{order.executed.price:.2f}, Cost={order.executed.value:.2f}, Comm={order.executed.comm:.2f}')
            self.order = None  # Resetting the entry request to the position

    def notify_trade(self, trade):
        """Changing the position status"""
        if trade.isclosed:  # If the position is closed
            self.log(f'Trade Profit, Gross={trade.pnl:.2f}, NET={trade.pnlcomm:.2f}')


if __name__ == '__main__':  # The entry point when running this script

    board = "TQBR"  # class of ticker
    symbol = 'SBER'  # ticker
    ticker = f"{board}.{symbol}"  # ticker TQBR.SBER

    cerebro = bt.Cerebro(stdstats=False, quicknotify=True)  # We initiate the BackTrader "engine". The standard statistics of transactions and the yield curve are not needed
    today = date.today()  # Today's date without time
    week_ago = today - timedelta(days=3)  # Date 3 days ago without time

    store = FinamStore(client_id=Config.ClientIds[0], access_token=Config.AccessToken)  # Storage Finam + authorization on Finam/Common
    broker = store.getbroker(use_positions=False)  # Broker Finam
    cerebro.setbroker(broker)  # set a broker

    data = store.getdata(dataname=ticker, timeframe=bt.TimeFrame.Minutes, compression=1, fromdate=week_ago, live_bars=True)  # Historical and new minute bars for all time
    cerebro.adddata(data)  # Adding data


    # ticker_info = store.get_symbol_info(board, symbol) # step_price , lots...

    cerebro.addsizer(bt.sizers.FixedSize, stake=10)  # Number of shares in pieces for purchase/sale
    # cerebro.addsizer(bt.sizers.FixedSize, stake=1)  # Number of futures in pieces for purchase/sale

    cerebro.addstrategy(LimitCancel, timeframe="M1", LimitPct=1, ticker_info={"step_price": 0.01})  # Adding a trading system with a limit entry in n%
    cerebro.run()  # Launching a trading system
