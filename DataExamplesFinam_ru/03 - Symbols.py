import datetime as dt
import backtrader as bt
from Strategy import StrategyJustPrintsOHLCVAndSuperCandles  # Торговая система

from backtrader_finam.finam_store import FinamStore  # Storage Finam
from my_config.Config_Finam import Config  # for authorization on Finam/Common


# Несколько тикеров для нескольких торговых систем по одному временнОму интервалу history + live
if __name__ == '__main__':  # Точка входа при запуске этого скрипта
    
    tickers = ('TQBR.SBER', 'TQBR.AFLT')  # тикеры, по которым будем получать данные

    store = FinamStore(client_id=Config.ClientIds[0], access_token=Config.AccessToken)  # Storage Finam + authorization on Finam/Common
    cerebro = bt.Cerebro(quicknotify=True)

    for ticker in tickers:  # Пробегаемся по всем тикерам

        # 1. Исторические 5-минутные бары за последние 120 часов + График т.к. оффлайн/ таймфрейм M5
        fromdate = dt.datetime.utcnow() - dt.timedelta(minutes=120*60)  # берем данные за последние 120 часов
        data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=5, dataname=ticker, fromdate=fromdate, live_bars=False)

        # 2. Исторические 1-минутные бары за прошлый час + новые live бары / таймфрейм M1
        # fromdate = dt.datetime.utcnow() - dt.timedelta(minutes=60)  # берем данные за последний 1 час
        # data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=1, dataname=ticker, fromdate=fromdate, live_bars=True)

        # 3. Исторические 1-часовые бары за неделю + График т.к. оффлайн/ таймфрейм H1
        # fromdate = dt.datetime.utcnow() - dt.timedelta(hours=24*7)  # берем данные за последнюю неделю от текущего времени
        # data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=60, dataname=ticker, fromdate=fromdate, live_bars=False)

        cerebro.adddata(data)  # Добавляем данные

    cerebro.addstrategy(StrategyJustPrintsOHLCVAndSuperCandles)  # Добавляем торговую систему

    cerebro.run()  # Запуск торговой системы
    cerebro.plot()  # Рисуем график !!! ЕСЛИ, никаких данных с рынка не получили, то здесь будет AttributeError: 'Plot_OldSync' object has no attribute 'mpyplot'
