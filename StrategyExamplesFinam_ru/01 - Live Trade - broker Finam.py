# git clone https://github.com/cia76/FinamPy
# pip install pytz grpcio google protobuf google-cloud-datastore

import datetime as dt
import backtrader as bt

# пример live торговли для Finam
from FinamPy import FinamPy  # Коннект к Финам API - для выставления заявок на покупку/продажу
from FinamPy.proto.tradeapi.v1.common_pb2 import BUY_SELL_BUY, BUY_SELL_SELL

from backtrader_finam.finam_store import FinamStore  # Storage Finam
from my_config.Config_Finam import Config  # для авторизации на Finam/Common


# Торговая система
class RSIStrategy(bt.Strategy):
    """
    Демонстрация live стратегии - однократно покупаем по рынку 1 лот и однократно продаем его по рынку через 3 бара
    """
    params = (  # Параметры торговой системы
        ('timeframe', ''),
        ('live_prefix', ''),  # префикс для выставления заявок в live
        ('info_tickers', []),  # информация по тикерам
        ('fp_provider', ''),  # Коннект к Финам API - для выставления заявок на покупку/продажу
        ('client_id', ''),  # Коннект к Финам API - для выставления заявок на покупку/продажу
        ('security_board', ''),  # Коннект к Финам API - для выставления заявок на покупку/продажу
    )

    def __init__(self):
        """Инициализация, добавление индикаторов для каждого тикера"""
        self.orders = {}  # Организовываем заявки в виде справочника, конкретно для этой стратегии один тикер - одна активная заявка
        for d in self.datas:  # Пробегаемся по всем тикерам
            self.orders[d._name] = None  # Заявки по тикеру пока нет

        # создаем индикаторы для каждого тикера
        self.sma1 = {}
        self.sma2 = {}
        self.rsi = {}
        for i in range(len(self.datas)):
            ticker = list(self.dnames.keys())[i]    # key name is ticker name
            self.sma1[ticker] = bt.indicators.SMA(self.datas[i], period=8)  # SMA indicator
            self.sma2[ticker] = bt.indicators.SMA(self.datas[i], period=16)  # SMA indicator
            self.rsi[ticker] = bt.indicators.RSI(self.datas[i], period=14)  # RSI indicator

        self.buy_once = {}
        self.sell_once = {}
        self.order_time = None
        self.client_id = self.p.client_id
        self.security_board = self.p.security_board

    def start(self):
        for d in self.datas:  # Running through all the tickers
            self.buy_once[d._name] = False
            self.sell_once[d._name] = False

    def next(self):
        """Приход нового бара тикера"""
        for data in self.datas:  # Пробегаемся по всем запрошенным барам всех тикеров
            ticker = data._name
            status = data._state  # 0 - Live data, 1 - History data, 2 - None
            _interval = self.p.timeframe
            _date = bt.num2date(data.datetime[0])

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
                print(f'\t - {ticker} RSI : {self.rsi[ticker][0]}')

                if status != 0: continue  # если не live - то не входим в позицию!

                print(f"\t - Free balance: {self.broker.getcash()}")

                if not self.buy_once[ticker]:  # Enter long
                    free_money = self.broker.getcash()
                    print(f" - free_money: {free_money}")

                    # lot = self.p.info_tickers[ticker]['securities']['LOTSIZE']
                    # size = 1 * lot  # купим 1 лот - проверку на наличие денег не будем делать, считаем что они есть)
                    # price = self.format_price(ticker, data.close[0] * 0.995)  # buy at close price -0.005% - to prevent buy
                    # # price = 273.65
                    # print(f" - buy {ticker} size = {size} at price = {price}")

                    # self.orders[data._name] = self.buy(data=data, exectype=bt.Order.Limit, price=price, size=size)
                    rez = self.p.fp_provider.new_order(client_id=self.client_id, security_board=self.security_board,
                                                       security_code=ticker,
                                                       buy_sell=BUY_SELL_BUY, quantity=1,
                                                       use_credit=True,
                                                       )  # price не указываем, чтобы купить по рынку

                    self.order_time = dt.datetime.now()
                    print(f"Выставили заявку на покупку 1 лота {ticker}:", rez)
                    print("\t - транзакция:", rez.transaction_id)
                    print("\t - время:", self.order_time)

                    # print(f"\t - Выставлена заявка {self.orders[data._name]} на покупку {data._name}")

                    self.buy_once[ticker] = len(self)  # для однократной покупки + записываем номер бара

                else:  # Если есть позиция, т.к. покупаем сразу по рынку
                    print(self.sell_once[ticker], self.buy_once[ticker], len(self), len(self) > self.buy_once[ticker] + 3)
                    if not self.sell_once[ticker]:  # если мы еще не продаём
                        if self.buy_once[ticker] and len(self) > self.buy_once[ticker] + 3:  # если у нас есть позиция на 3-м баре после покупки
                            print("sell")
                            print(f"\t - Продаём по рынку {data._name}...")

                            # self.orders[data._name] = self.close()  # закрываем позицию по рынку
                            rez = self.p.fp_provider.new_order(client_id=self.client_id, security_board=self.security_board,
                                                               security_code=ticker,
                                                               buy_sell=BUY_SELL_SELL, quantity=1,
                                                               use_credit=True,
                                                               )  # price не указываем, чтобы купить по рынку
                            self.order_time = None

                            print(f"Выставили заявку на продажу 1 лота {ticker}:", rez)
                            print("\t - транзакция:", rez.transaction_id)
                            print("\t - время:", self.order_time)

                            self.sell_once[ticker] = True  # для предотвращения повторной продажи

    def notify_order(self, order):
        """Изменение статуса заявки"""
        order_data_name = order.data._name  # Имя тикера из заявки
        print("*"*50)
        self.log(f'Заявка номер {order.ref} {order.info["order_number"]} {order.getstatusname()} {"Покупка" if order.isbuy() else "Продажа"} {order_data_name} {order.size} @ {order.price}')
        if order.status == bt.Order.Completed:  # Если заявка полностью исполнена
            if order.isbuy():  # Заявка на покупку
                self.log(f'Покупка {order_data_name} Цена: {order.executed.price:.2f}, Объём: {order.executed.value:.2f}, Комиссия: {order.executed.comm:.2f}')
            else:  # Заявка на продажу
                self.log(f'Продажа {order_data_name} Цена: {order.executed.price:.2f}, Объём: {order.executed.value:.2f}, Комиссия: {order.executed.comm:.2f}')
                self.orders[order_data_name] = None  # Сбрасываем заявку на вход в позицию
        print("*" * 50)

    def notify_trade(self, trade):
        """Изменение статуса позиции"""
        if trade.isclosed:  # Если позиция закрыта
            self.log(f'Прибыль по закрытой позиции {trade.getdataname()} Общая={trade.pnl:.2f}, Без комиссии={trade.pnlcomm:.2f}')

    def log(self, txt, dt=None):
        """Вывод строки с датой на консоль"""
        dt = bt.num2date(self.datas[0].datetime[0]) if not dt else dt  # Заданная дата или дата текущего бара
        print(f'{dt.strftime("%d.%m.%Y %H:%M")}, {txt}')  # Выводим дату и время с заданным текстом на консоль

    def format_price(self, ticker, price):
        """
        Функция округления до шага цены step, сохраняя signs знаков после запятой
        print(round_custom_f(0.022636, 0.000005, 6)) --> 0.022635
        """
        step = self.p.info_tickers[ticker]['securities']['MINSTEP']  # сохраняем минимальный Шаг цены
        signs = self.p.info_tickers[ticker]['securities']['DECIMALS']  # сохраняем Кол-во десятичных знаков

        val = round(price / step) * step
        return float(("{0:." + str(signs) + "f}").format(val))


def get_some_info_for_tickers(tickers, live_prefix):
    """Функция для получения информации по тикерам"""
    info = {}
    for ticker in tickers:
        _point = ticker.index('.')
        board = ticker[0:_point]  # Класс тикера
        symbol = ticker[_point + 1:]  # Тикер +1 для точки
        i = store.get_symbol_info(board, symbol)
        info[f"{live_prefix}{ticker}"] = i
    return info


if __name__ == '__main__':
    # пример для Финам
    live_prefix = ''  # префикс для выставления заявок в live
    fp_provider = FinamPy(Config.AccessToken)  # Коннект к Финам API - для выставления заявок на покупку/продажу
    client_id = Config.ClientIds[0]  # id клиента

    security_board = "TQBR"  # класс тикеров
    symbol = 'SBER'  # Тикер
    # symbol2 = 'LKOH'  # Тикер

    ticker = f"{security_board}.{symbol}"
    # ticker2 = f"{security_board}.{symbol2}"

    store = FinamStore(client_id=Config.ClientIds[0], access_token=Config.AccessToken)  # Storage Finam + authorization on Finam/Common
    cerebro = bt.Cerebro(quicknotify=True)  # Initiating the "engine" BackTrader

    # live подключение к брокеру будем делать напрямую

    # ----------------------------------------------------
    # Внимание! - Теперь это Live режим работы стратегии #
    # ----------------------------------------------------

    info_tickers = get_some_info_for_tickers([ticker, ], live_prefix)  # берем информацию о тикере (минимальный шаг цены, кол-во знаков после запятой)

    # live 1-минутные бары / таймфрейм M1
    timeframe = "M1"
    fromdate = dt.datetime.utcnow()
    data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=1, dataname=ticker, fromdate=fromdate,
                         live_bars=True, name=f"{live_prefix}{ticker}")  # поставьте здесь True - если нужно получать live бары # name - нужен для выставления в live заявок
    # data2 = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=1, dataname=symbol2, fromdate=fromdate, live_bars=True)  # поставьте здесь True - если нужно получать live бары

    cerebro.adddata(data)  # Добавляем данные
    # cerebro.adddata(data2)  # Добавляем данные

    cerebro.addstrategy(RSIStrategy, timeframe=timeframe, live_prefix=live_prefix, info_tickers=info_tickers,
                        fp_provider=fp_provider,
                        client_id=client_id,
                        security_board=security_board)  # Добавляем торговую систему

    cerebro.run()  # Запуск торговой системы
    # cerebro.plot()  # Рисуем график - в live режиме не нужно
