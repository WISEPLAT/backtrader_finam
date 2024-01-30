from datetime import date, timedelta
import decimal
import backtrader as bt

from backtrader_finam.finam_store import FinamStore  # Storage Finam
from my_config.Config_Finam import Config  # для авторизации на Finam/Common


class LimitCancel(bt.Strategy):
    """
    Выставляем заявку на покупку на n% ниже цены закрытия
    Если за 1 бар заявка не срабатывает, то закрываем ее
    Если срабатывает, то закрываем позицию. Неважно, с прибылью или убытком
    """
    params = (  # Параметры торговой системы
        ('timeframe', ''),
        ('LimitPct', 1),  # Заявка на покупку на n% ниже цены закрытия
        ('ticker_info', ''),
    )

    def __init__(self):
        """Инициализация торговой системы"""
        self.order = None  # Заявка на вход/выход из позиции

    def next(self):
        """Приход нового бара тикера"""
        for data in self.datas:  # Пробегаемся по всем запрошенным барам всех тикеров
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
                if self.order and self.order.status == bt.Order.Submitted:  # Если заявка не исполнена (отправлена брокеру)
                    return  # то ждем исполнения, выходим, дальше не продолжаем

                # print(2222, self.position, len(self.position), bool(self.position), not self.position, type(self.position))

                if not self.position or (self.position and self.position.size <= 30):  # Если позиции нет
                    if self.order and self.order.status == bt.Order.Accepted:  # Если заявка не исполнена (принята брокером)
                        print("Let's Cancel order.")
                        self.cancel(self.order)  # то снимаем ее
                    limit_price = self.data.close[0] * (1 - self.p.LimitPct / 100)  # На n% ниже цены закрытия
                    print(f"Our limit price: {limit_price}")
                    # price should be div by step_price
                    limit_price = (limit_price // self.p.ticker_info["step_price"]) * self.p.ticker_info["step_price"]
                    limit_price = decimal.Decimal(limit_price)
                    print(f"Our limit price OK: {limit_price}")
                    self.order = self.buy(exectype=bt.Order.Limit, price=limit_price, use_credit=True)  # Лимитная заявка на покупку
                    print("Order was submitted.")
                else:  # Если позиция есть
                    self.order = self.close()  # Заявка на закрытие позиции по рыночной цене
                    print("Order was closed.")

    def notify_trade(self, trade):
        """Изменение статуса позиции"""
        if trade.isclosed:  # Если позиция закрыта
            self.log(f'Прибыль по закрытой позиции {trade.getdataname()} Общая={trade.pnl:.2f}, Без комиссии={trade.pnlcomm:.2f}')

    def log(self, txt, dt=None):
        """Вывод строки с датой на консоль"""
        dt = bt.num2date(self.datas[0].datetime[0]) if not dt else dt  # Заданная дата или дата текущего бара
        print(f'{dt.strftime("%d.%m.%Y %H:%M")}, {txt}')  # Выводим дату и время с заданным текстом на консоль

    def notify_order(self, order):
        """Изменение статуса заявки"""
        if order.status in (bt.Order.Created, bt.Order.Submitted, bt.Order.Accepted):  # Если заявка создана, отправлена брокеру, принята брокером (не исполнена)
            self.log(f'Alive Status: {order.getstatusname()}. TransId={order.ref}')
        elif order.status in (bt.Order.Canceled, bt.Order.Margin, bt.Order.Rejected, bt.Order.Expired):  # Если заявка отменена, нет средств, заявка отклонена брокером, снята по времени (снята)
            self.log(f'Cancel Status: {order.getstatusname()}. TransId={order.ref}')
        elif order.status == bt.Order.Partial:  # Если заявка частично исполнена
            self.log(f'Part Status: {order.getstatusname()}. TransId={order.ref}')
        elif order.status == bt.Order.Completed:  # Если заявка полностью исполнена
            if order.isbuy():  # Заявка на покупку
                self.log(f'Bought @{order.executed.price:.2f}, Cost={order.executed.value:.2f}, Comm={order.executed.comm:.2f}')
            elif order.issell():  # Заявка на продажу
                self.log(f'Sold @{order.executed.price:.2f}, Cost={order.executed.value:.2f}, Comm={order.executed.comm:.2f}')
            self.order = None  # Сбрасываем заявку на вход в позицию

    def notify_trade(self, trade):
        """Изменение статуса позиции"""
        if trade.isclosed:  # Если позиция закрыта
            self.log(f'Trade Profit, Gross={trade.pnl:.2f}, NET={trade.pnlcomm:.2f}')


if __name__ == '__main__':  # Точка входа при запуске этого скрипта

    board = "TQBR"  # класс тикеров
    symbol = 'SBER'  # Тикер
    ticker = f"{board}.{symbol}"  # Тикер TQBR.SBER

    cerebro = bt.Cerebro(stdstats=False, quicknotify=True)  # Инициируем "движок" BackTrader. Стандартная статистика сделок и кривой доходности не нужна
    today = date.today()  # Сегодняшняя дата без времени
    week_ago = today - timedelta(days=3)  # Дата 3 дня назад без времени

    store = FinamStore(client_id=Config.ClientIds[0], access_token=Config.AccessToken)  # Storage Finam + авторизация на Finam/Common
    broker = store.getbroker(use_positions=False)  # Брокер Finam
    cerebro.setbroker(broker)  # Устанавливаем брокера

    data = store.getdata(dataname=ticker, timeframe=bt.TimeFrame.Minutes, compression=1, fromdate=week_ago, live_bars=True)  # Исторические и новые минутные бары за все время
    cerebro.adddata(data)  # Добавляем данные


    # ticker_info = store.get_symbol_info(board, symbol) # step_price , lots...

    cerebro.addsizer(bt.sizers.FixedSize, stake=10)  # Кол-во акций в штуках для покупки/продажи
    # cerebro.addsizer(bt.sizers.FixedSize, stake=1)  # Кол-во фьючерсов в штуках для покупки/продажи

    cerebro.addstrategy(LimitCancel, timeframe="M1", LimitPct=1, ticker_info={"step_price": 0.01})  # Добавляем торговую систему с лимитным входом в n%
    cerebro.run()  # Запуск торговой системы
