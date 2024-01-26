from datetime import date, datetime, timedelta
from backtrader import Cerebro, TimeFrame
from Strategy import StrategyJustPrintsOHLCVAndSuperCandles  # Trading System

from backtrader_finam.finam_store import FinamStore  # Storage Finam
from my_config.Config_Finam import Config  # for authorization on Finam/Common


# Historical/new bars of ticker
if __name__ == '__main__':  # Entry point when running this script

    board = 'TQBR'
    symbol = 'SBER'
    ticker = f"{board}.{symbol}"
    ticker2 = "TQBR.GAZP"

    store = FinamStore(client_id=Config.ClientIds[0], access_token=Config.AccessToken)  # Storage Finam + authorization on Finam/Common
    cerebro = Cerebro(stdstats=False)  # Initiating the "engine" BackTrader

    today = date.today()  # Today's date without time
    week_ago = today - timedelta(days=7)  # a week ago
    days_ago_5 = today - timedelta(days=5)  # three days ago
    days_ago_10 = today - timedelta(days=10)  # ten days ago
    days_ago_N = today - timedelta(days=30)  # N days ago

    # 1. All historical daytime bars for the week
    # data = store.getdata(dataname=ticker, timeframe=TimeFrame.Days, fromdate=week_ago)

    # 2. Historical 30-minute bars from a given date a week ago to the last bar (resample from M10)
    # data = store.getdata(dataname=ticker, timeframe=TimeFrame.Minutes, compression=30, fromdate=week_ago)

    # 3. Historical 5-minute bars of the first hour of the current session without the first 5 minutes
    # data = store.getdata(dataname=ticker, timeframe=TimeFrame.Minutes, compression=5, fromdate=datetime(today.year, today.month, today.day, 10, 5), todate=datetime(today.year, today.month, today.day, 10, 55))

    # 4. Historical and new 1-minute bars from the beginning of today's session (history + live M1)
    # data = store.getdata(dataname=ticker, timeframe=TimeFrame.Minutes, compression=1, fromdate=today, live_bars=True)

    # 5. Historical and new 10-minute bars (history + live M10)
    # data = store.getdata(dataname=ticker, timeframe=TimeFrame.Minutes, compression=10, fromdate=days_ago_5, live_bars=True)

    # 6. Historical and new 5-minute bars (history + live M5 resample from M1)
    # data = store.getdata(dataname=ticker, timeframe=TimeFrame.Minutes, compression=5, fromdate=days_ago_5, live_bars=True)  # An example with TF M5, which is not in the data, it is obtained from '1m' (resample)

    # # 7. Historical 5-minute bars for ONE ticker
    # data = store.getdata(dataname=ticker, timeframe=TimeFrame.Minutes, compression=5, fromdate=days_ago_5, live_bars=False)

    # # 8. Historical 1-minute LIVE bars for TWO tickers
    # data = store.getdata(dataname=ticker, timeframe=TimeFrame.Minutes, compression=1, fromdate=days_ago_5, live_bars=True)
    # data2 = store.getdata(dataname=ticker2, timeframe=TimeFrame.Minutes, compression=1, fromdate=days_ago_5, live_bars=True)

    # 9. Historical 1-minute LIVE bars for TWO tickers
    data = store.getdata(dataname=ticker, timeframe=TimeFrame.Minutes, compression=5, fromdate=days_ago_5, live_bars=True)
    data2 = store.getdata(dataname=ticker2, timeframe=TimeFrame.Minutes, compression=5, fromdate=days_ago_5, live_bars=True)

    cerebro.adddata(data)  # Adding data
    cerebro.adddata(data2)  # Adding data2

    cerebro.addstrategy(StrategyJustPrintsOHLCVAndSuperCandles)   # Adding a trading system
    cerebro.run()  # Launching a trading system
    cerebro.plot(style='candle')  # Draw a chart !!! IF we have not received any data from the market, then here it will be AttributeError: 'Plot_OldSync' object has no attribute 'mpyplot'
