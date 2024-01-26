import datetime as dt
import backtrader as bt
from Strategy import StrategyJustPrintsOHLCVAndSuperCandles  # Trading System

from backtrader_finam.finam_store import FinamStore  # Storage Finam
from my_config.Config_Finam import Config  # for authorization on Finam/Common


def get_timeframe(tf, TimeFrame):
    """Converting TF to parameters for adding strategy data"""
    interval = 1  # by default, the timeframe is 1m
    _timeframe = TimeFrame.Minutes  # by default, the timeframe is 1m

    if tf == 'M1': interval = 1
    if tf == 'M5': interval = 5
    if tf == 'M10': interval = 10
    if tf == 'M15': interval = 15
    if tf == 'M30': interval = 30
    if tf == 'H1': interval = 60
    if tf == 'D1': _timeframe = TimeFrame.Days
    if tf == 'W1': _timeframe = TimeFrame.Weeks
    if tf == 'MN1': _timeframe = TimeFrame.Months
    return _timeframe, interval


# Gluing the ticker history from a file and Binance (Rollover)
if __name__ == '__main__':  # Entry point when running this script

    ticker = 'TQBR.SBER'  # Ticker in the format <Ticker code>

    store = FinamStore(client_id=Config.ClientIds[0], access_token=Config.AccessToken)  # Storage Finam + authorization on Finam/Common
    cerebro = bt.Cerebro(quicknotify=True)

    tf = "D1"  # '1m', '10m', '1h', '1D', '1W', '1M'
    _t, _c = get_timeframe(tf, bt.TimeFrame)

    d1 = bt.feeds.GenericCSVData(  # We get the history from the file - which does not contain the last 5 days
        timeframe=_t, compression=_c,  # to be in the same TF as d2
        dataname=f'{ticker}_{tf}_minus_5_days.csv',  # File to import from MOEX. Created from example 02 - Symbol data to DF.py
        separator=',',  # Columns are separated by commas
        dtformat='%Y-%m-%d',  # dtformat='%Y-%m-%d %H:%M:%S',  # Date/time format YYYY-MM-DD HH:MM:SS
        openinterest=-1,  # There is no open interest in the file
        sessionend=dt.time(0, 0),  # For daily data and above, the end time of the session is substituted. To coincide with the story, you need to set the closing time to 00:00
    )

    fromdate = dt.datetime.utcnow() - dt.timedelta(days=15)  # we take data for the last 15 days
    d2 = store.getdata(timeframe=_t, compression=_c, dataname=ticker, fromdate=fromdate, live_bars=False)  # Historical data for the smallest time interval

    cerebro.rolloverdata(d1, d2, name=ticker)  # Glued ticker

    cerebro.addstrategy(StrategyJustPrintsOHLCVAndSuperCandles)  # Adding a trading system

    cerebro.run()  # Launching a trading system
    cerebro.plot()  # Draw a chart !!! IF we have not received any data from the market, then here it will be AttributeError: 'Plot_OldSync' object has no attribute 'mpyplot'
