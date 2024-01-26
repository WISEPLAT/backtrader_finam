import datetime as dt
import backtrader as bt
from Strategy import StrategyJustPrintsOHLCVAndSuperCandles  # Торговая система

from backtrader_finam.finam_store import FinamStore  # Storage Finam
from my_config.Config_Finam import Config  # for authorization on Finam/Common


def get_timeframe(tf, TimeFrame):
    """Преобразуем ТФ в параметры для добавления данных по стратегии"""
    interval = 1  # по умолчанию таймфрейм минутный
    _timeframe = TimeFrame.Minutes  # по умолчанию таймфрейм минутный

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


# Склейка истории тикера из файла и Binance (Rollover)
if __name__ == '__main__':  # Точка входа при запуске этого скрипта

    ticker = 'TQBR.SBER'  # Тикер

    store = FinamStore(client_id=Config.ClientIds[0], access_token=Config.AccessToken)  # Storage Finam + authorization on Finam/Common
    cerebro = bt.Cerebro(quicknotify=True)

    tf = "D1"  # '1m', '10m', '1h', '1D', '1W', '1M'
    _t, _c = get_timeframe(tf, bt.TimeFrame)

    d1 = bt.feeds.GenericCSVData(  # Получаем историю из файла - в котором нет последних 5 дней
        timeframe=_t, compression=_c,  # что-бы был тот же ТФ как и у d2
        dataname=f'{ticker}_{tf}_minus_5_days.csv',  # Файл для импорта из MOEX. Создается из примера 02 - Symbol data to DF.py
        separator=',',  # Колонки разделены запятой
        dtformat='%Y-%m-%d',  # dtformat='%Y-%m-%d %H:%M:%S',  # Формат даты/времени YYYY-MM-DD HH:MM:SS
        openinterest=-1,  # Открытого интереса в файле нет
        sessionend=dt.time(0, 0),  # Для дневных данных и выше подставляется время окончания сессии. Чтобы совпадало с историей, нужно поставить закрытие на 00:00
    )

    fromdate = dt.datetime.utcnow() - dt.timedelta(days=15)  # берем данные за последние 15 дней
    d2 = store.getdata(timeframe=_t, compression=_c, dataname=ticker, fromdate=fromdate, live_bars=False)  # Исторические данные по самому меньшему временному интервалу

    cerebro.rolloverdata(d1, d2, name=ticker)  # Склеенный тикер

    cerebro.addstrategy(StrategyJustPrintsOHLCVAndSuperCandles)  # Добавляем торговую систему

    cerebro.run()  # Запуск торговой системы
    cerebro.plot()  # Рисуем график !!! ЕСЛИ, никаких данных с рынка не получили, то здесь будет AttributeError: 'Plot_OldSync' object has no attribute 'mpyplot'
