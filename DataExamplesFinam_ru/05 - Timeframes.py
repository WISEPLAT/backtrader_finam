import datetime as dt
import backtrader as bt
from Strategy import StrategyJustPrintsOHLCVAndSuperCandles  # Торговая система

from backtrader_finam.finam_store import FinamStore  # Storage Finam
from my_config.Config_Finam import Config  # for authorization on Finam/Common


# Несколько временнЫх интервалов по одному тикеру: Получение из истории + live
if __name__ == '__main__':  # Точка входа при запуске этого скрипта

    ticker = 'TQBR.SBER'  # Тикер

    store = FinamStore(client_id=Config.ClientIds[0], access_token=Config.AccessToken)  # Storage Finam + authorization on Finam/Common
    cerebro = bt.Cerebro(quicknotify=True)

    # 1. Исторические 5-минутные бары + 10-минутные за последние 120 часов + График т.к. оффлайн/ таймфрейм M5 + M10
    fromdate = dt.datetime.utcnow() - dt.timedelta(minutes=120*60)  # берем данные за последние 120 часов
    data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=5, dataname=ticker, fromdate=fromdate, live_bars=False)  # Исторические данные по малому временнОму интервалу (должен идти первым)
    cerebro.adddata(data)  # Добавляем данные
    data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=10, dataname=ticker, fromdate=fromdate, live_bars=False)  # Исторические данные по большому временнОму интервалу

    # # 2. Исторические 1-минутные + 5-минутные бары за прошлые 5 дней + новые live бары / таймфрейм M1 + M5
    # fromdate = dt.datetime.utcnow() - dt.timedelta(days=5)  # берем данные за последний 1 час
    # data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=1, dataname=ticker, fromdate=fromdate, live_bars=True)  # Исторические данные по малому временнОму интервалу (должен идти первым)
    # cerebro.adddata(data)  # Добавляем данные
    # data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=5, dataname=ticker, fromdate=fromdate, live_bars=True)  # Исторические данные по большому временнОму интервалу

    # # 3. Исторические 1-часовые бары + дневные за неделю + График т.к. оффлайн/ таймфрейм H1 + D1
    # fromdate = dt.datetime.utcnow() - dt.timedelta(hours=24*7)  # берем данные за последнюю неделю от текущего времени
    # data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=60, dataname=ticker, fromdate=fromdate, live_bars=False)  # Исторические данные по малому временнОму интервалу (должен идти первым)
    # cerebro.adddata(data)  # Добавляем данные
    # data = store.getdata(timeframe=bt.TimeFrame.Days, compression=1, dataname=ticker, fromdate=fromdate, live_bars=False)  # Исторические данные по большому временнОму интервалу

    cerebro.adddata(data)  # Добавляем данные
    cerebro.addstrategy(StrategyJustPrintsOHLCVAndSuperCandles)  # Добавляем торговую систему

    cerebro.run()  # Запуск торговой системы
    cerebro.plot()  # Рисуем график !!! ЕСЛИ, никаких данных с рынка не получили, то здесь будет AttributeError: 'Plot_OldSync' object has no attribute 'mpyplot'
