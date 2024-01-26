import datetime as dt
import backtrader as bt
from Strategy import StrategyJustPrintsOHLCVAndSuperCandles  # Trading System

from backtrader_finam.finam_store import FinamStore  # Storage Finam
from my_config.Config_Finam import Config  # for authorization on Finam/Common


# Multiple tickers for multiple trading systems on the same time interval history + live
if __name__ == '__main__':  # Entry point when running this script
    
    tickers = ('TQBR.SBER', 'TQBR.AFLT')  # tickers for which we will receive data

    store = FinamStore(client_id=Config.ClientIds[0], access_token=Config.AccessToken)  # Storage Finam + authorization on Finam/Common
    cerebro = bt.Cerebro(quicknotify=True)

    for ticker in tickers:  # Running through all the tickers

        # 1. Historical 5-minute bars for the last 120 hours + Chart because offline/ M5 timeframe
        fromdate = dt.datetime.utcnow() - dt.timedelta(minutes=120*60)  # we take data for the last 120 hours
        data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=5, dataname=ticker, fromdate=fromdate, live_bars=False)

        # 2. Historical 1-minute bars for the last hour + new live bars / M1 timeframe
        # fromdate = dt.datetime.utcnow() - dt.timedelta(minutes=60)  # we take the data for the last 1 hour
        # data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=1, dataname=ticker, fromdate=fromdate, live_bars=True)

        # 3. Historical 1-hour bars for the week + Chart because offline/ timeframe H1
        # fromdate = dt.datetime.utcnow() - dt.timedelta(hours=24*7)  # we take the data for the last week from the current time
        # data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=60, dataname=ticker, fromdate=fromdate, live_bars=False)

        cerebro.adddata(data)  # Adding data

    cerebro.addstrategy(StrategyJustPrintsOHLCVAndSuperCandles)  # Adding a trading system

    cerebro.run()  # Launching a trading system
    cerebro.plot()  # Draw a chart !!! IF we have not received any data from the market, then here it will be AttributeError: 'Plot_OldSync' object has no attribute 'mpyplot'
