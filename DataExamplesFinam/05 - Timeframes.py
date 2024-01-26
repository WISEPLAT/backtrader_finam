import datetime as dt
import backtrader as bt
from Strategy import StrategyJustPrintsOHLCVAndSuperCandles  # Trading System

from backtrader_finam.finam_store import FinamStore  # Storage Finam
from my_config.Config_Finam import Config  # for authorization on Finam/Common


# Multiple time intervals for one ticker: Getting from history + live
if __name__ == '__main__':  # Entry point when running this script

    ticker = 'TQBR.SBER'  # Ticker in the format <Ticker code>

    store = FinamStore(client_id=Config.ClientIds[0], access_token=Config.AccessToken)  # Storage Finam + authorization on Finam/Common
    cerebro = bt.Cerebro(quicknotify=True)

    # 1. Historical 5-minute bars + 10-minute bars for the last 120 hours + Chart because offline/ timeframe M5 + M10
    fromdate = dt.datetime.utcnow() - dt.timedelta(minutes=120*60)  # we take data for the last 120 hours
    data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=5, dataname=ticker, fromdate=fromdate, live_bars=False)  # Historical data for a small time interval (should go first)
    cerebro.adddata(data)  # Добавляем данные
    data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=10, dataname=ticker, fromdate=fromdate, live_bars=False)  # Historical data for a large time interval

    # # 2. Historical 1-minute + 5-minute bars for the last 5 days + new live bars / timeframe M1 + M5
    # fromdate = dt.datetime.utcnow() - dt.timedelta(days=5)  # we take data for the last 5 days
    # data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=1, dataname=ticker, fromdate=fromdate, live_bars=True)  # Historical data for a small time interval (should go first)
    # cerebro.adddata(data)  # Adding data
    # data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=5, dataname=ticker, fromdate=fromdate, live_bars=True)  # Historical data for a large time interval

    # # 3. Historical 1-hour bars + 1-day bars for the week + Chart because offline/ timeframe H1 + D1
    # fromdate = dt.datetime.utcnow() - dt.timedelta(hours=24*7)  # we take data for the last 7 days
    # data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=60, dataname=ticker, fromdate=fromdate, live_bars=False)  # Historical data for a small time interval (should go first)
    # cerebro.adddata(data)  # Adding data
    # data = store.getdata(timeframe=bt.TimeFrame.Days, compression=1, dataname=ticker, fromdate=fromdate, live_bars=False)  # Historical data for a large time interval

    cerebro.adddata(data)  # Adding data
    cerebro.addstrategy(StrategyJustPrintsOHLCVAndSuperCandles)  # Adding a trading system

    cerebro.run()  # Launching a trading system
    cerebro.plot()  # Draw a chart !!! IF we have not received any data from the market, then here it will be AttributeError: 'Plot_OldSync' object has no attribute 'mpyplot'
