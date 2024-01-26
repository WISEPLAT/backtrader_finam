import datetime as dt
import backtrader as bt
import pandas as pd

from backtrader_finam.finam_store import FinamStore  # Storage Finam
from my_config.Config_Finam import Config  # for authorization on Finam/Common


# Торговая система
class StrategySaveOHLCVToDF(bt.Strategy):
    """Сохраняет OHLCV в DF"""
    params = (  # Параметры торговой системы
    )

    def __init__(self):
        self.df = {}
        self.df_tf = {}

    def start(self):
        for data in self.datas:  # Пробегаемся по всем запрошенным тикерам
            ticker = data._name
            self.df[ticker] = []
            _, self.df_tf[ticker] = store.get_interval(data._timeframe, data._compression)

    def next(self):
        """Приход нового бара тикера"""
        for data in self.datas:  # Пробегаемся по всем запрошенным тикерам
            ticker = data._name
            _date = bt.num2date(data.datetime[0])

            try:
                status = data._state  # 0 - Live data, 1 - History data, 2 - None
                _interval = data.interval
            except Exception as e:
                if data.resampling == 1:
                    status = 22
                    _, _interval = store.get_interval(data._timeframe, data._compression)
                    _interval = f"_{_interval}"
                else:
                    print("Error:", e)

            if status == 1:
                _state = "Resampled Data"
                if status == 1: _state = "False - History data"
                if status == 0: _state = "True - Live data"

                self.df[ticker].append([bt.num2date(data.datetime[0]), data.open[0], data.high[0], data.low[0], data.close[0], int(data.volume[0])])

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


# Исторические/новые бары тикера
if __name__ == '__main__':  # Точка входа при запуске этого скрипта
    board = 'TQBR'
    symbol = 'SBER'
    ticker = f"{board}.{symbol}"

    store = FinamStore(client_id=Config.ClientIds[0], access_token=Config.AccessToken)  # Storage Finam + authorization on Finam/Common
    cerebro = bt.Cerebro(quicknotify=True)

    # 1. Исторические D1 бары за 365 дней + График т.к. оффлайн/ таймфрейм D1
    fromdate = dt.datetime.utcnow() - dt.timedelta(days=365)  # берем данные за 365 дней от текущего времени
    data = store.getdata(timeframe=bt.TimeFrame.Days, compression=1, dataname=ticker, fromdate=fromdate, live_bars=False)

    cerebro.adddata(data)  # Добавляем данные
    cerebro.addstrategy(StrategySaveOHLCVToDF, )  # Добавляем торговую систему

    results = cerebro.run()  # Запуск торговой системы

    print(results[0].df)

    df = pd.DataFrame(results[0].df[ticker], columns=["datetime", "open", "high", "low", "close", "volume"])
    print(df)

    tf = results[0].df_tf[ticker]

    # save to file
    df.to_csv(f"{ticker}_{tf}.csv", index=False)

    # save to file
    df[:-5].to_csv(f"{ticker}_{tf}_minus_5_days.csv", index=False)

    cerebro.plot()  # Рисуем график !!! ЕСЛИ, никаких данных с рынка не получили, то здесь будет AttributeError: 'Plot_OldSync' object has no attribute 'mpyplot'
