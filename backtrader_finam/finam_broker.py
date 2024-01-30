from datetime import datetime
from typing import Union  # Объединение типов
from collections import defaultdict, deque, OrderedDict

from backtrader import BrokerBase, Order, BuyOrder, SellOrder
from backtrader.position import Position
from backtrader.utils.py3 import with_metaclass

from FinamPy.proto.tradeapi.v1.common_pb2 import BUY_SELL_BUY, BUY_SELL_SELL, OrderValidBefore, OrderValidBeforeType
from FinamPy.proto.tradeapi.v1.orders_pb2 import OrderStatus
from FinamPy.proto.tradeapi.v1.stops_pb2 import StopLoss, StopQuantity, StopQuantityUnits
from FinamPy.proto.tradeapi.v1.events_pb2 import OrderEvent

from FinamPy import FinamPy


class MetaFinamBroker(BrokerBase.__class__):
    def __init__(self, name, bases, dct):
        super(MetaFinamBroker, self).__init__(name, bases, dct)  # Инициализируем класс брокера
        # FinamStore.BrokerCls = self  # Регистрируем класс брокера в хранилище Финам


class FinamBroker(with_metaclass(MetaFinamBroker, BrokerBase)):
    """Брокер Финам"""
    params = (
        ('use_positions', True),  # При запуске брокера подтягиваются текущие позиции с биржи
    )

    def __init__(self, store):
        super(FinamBroker, self).__init__()
        self.store = store
        self.provider: FinamPy = self.store.fp_provider  # Провайдер
        self.client_id = self.store.client_id  # Торговый счет
        self.order_trade_request_id = None  # Код подписки на заявки/сделки по счету

        self.notifs = deque()  # Очередь уведомлений брокера о заявках
        self.startingcash = self.cash = 0  # Стартовые и текущие свободные средства по счету
        self.startingvalue = self.value = 0  # Стартовая и текущая стоимость позиций
        self.cash_value = {}  # Справочник Свободные средства/Стоимость позиций
        self.positions = defaultdict(Position)  # Список позиций
        self.orders = OrderedDict()  # Список заявок, отправленных на биржу
        self.ocos = {}  # Список связанных заявок (One Cancel Others)
        self.pcs = defaultdict(deque)  # Очередь всех родительских/дочерних заявок (Parent - Children)

    def start(self):
        super(FinamBroker, self).start()
        self.provider.on_order = self.on_order  # Обработка заявок
        if self.p.use_positions:  # Если нужно при запуске брокера получить текущие позиции на бирже
            self.get_all_active_positions()  # то получаем их
        self.startingcash = self.cash = self.getcash()  # Стартовые и текущие свободные средства по счету
        self.startingvalue = self.value = self.getvalue()  # Стартовая и текущая стоимость позиций
        self.order_trade_request_id = self.provider.subscribe_order_trade([self.client_id])  # Подписываемся на заявки/позиции по счету

    def getcash(self):
        """Свободные средства по счету"""
        if self.store:  # .BrokerCls:  # Если брокер есть в хранилище
            cash = 0.0  # Будем набирать свободные средства по всем валютам с конвертацией в рубли
            response = self.provider.get_portfolio(self.client_id)  # Портфель по счету
            try:  # Пытаемся получить свободные средства
                for money in response.money:  # Пробегаемся по всем свободным средствам в валютах
                    cross_rate = next(item.cross_rate for item in response.currencies if item.name == money.currency)  # Кол-во рублей за единицу валюты
                    cash += money.balance * cross_rate  # Переводим в рубли и добавляем к свободным средствам
                self.cash = cash  # Свободные средства по каждому портфелю на каждой бирже
                return self.cash
            except AttributeError:  # Если сервер отключен, то свободные средства не придут
                return 0  # Выдаем пустое значение. Получим свободные средства когда сервер будет работать

    def getvalue(self, datas=None):
        """Стоимость позиции, позиций, всех позиций"""
        if self.store:  # .BrokerCls:  # Если брокер есть в хранилище
            value = 0.0  # Будем набирать стоимость позиций
            response = self.provider.get_portfolio(self.client_id)  # Портфель по счету
            if datas is not None:  # Если получаем по тикерам
                for data in datas:  # Пробегаемся по всем тикерам
                    board, symbol = self.provider.dataname_to_board_symbol(data._name)  # По тикеру получаем площадку и код тикера
                    try:  # Пытаемся
                        position = next(item for item in response.positions if item.security_code == symbol)  # получить позицию
                        cross_rate = next(item.cross_rate for item in response.currencies if item.name == position.currency)  # Кол-во рублей за единицу валюты
                        value += position.equity * cross_rate
                    except StopIteration:  # Если позиция не найдена
                        pass  # то переходим к следующему тикеру
            else:  # Если получаем по счету
                if response:
                    value = response.equity - self.getcash()  # то берем текущую оценку в рублях
                else:
                    value = self.getcash()
            self.value = value  # Стоимость позиций
        return self.value

    def getposition(self, data):
        """Позиция по тикеру
        Используется в strategy.py для закрытия (close) и ребалансировки (увеличения/уменьшения) позиции:
        - В процентах от портфеля (order_target_percent)
        - До нужного кол-ва (order_target_size)
        - До нужного объема (order_target_value)
        """
        return self.positions[data._name]  # Получаем позицию по тикеру или нулевую позицию, если тикера в списке позиций нет

    def buy(self, owner, data, size, price=None, plimit=None, exectype=None, valid=None, tradeid=0, oco=None, trailamount=None, trailpercent=None, parent=None, transmit=True, **kwargs):
        """Заявка на покупку"""
        order = self.create_order(owner, data, size, price, plimit, exectype, valid, oco, parent, transmit, True, **kwargs)
        self.notifs.append(order.clone())  # Уведомляем брокера о принятии/отклонении зявки на бирже
        return order

    def sell(self, owner, data, size, price=None, plimit=None, exectype=None, valid=None, tradeid=0, oco=None, trailamount=None, trailpercent=None, parent=None, transmit=True, **kwargs):
        """Заявка на продажу"""
        order = self.create_order(owner, data, size, price, plimit, exectype, valid, oco, parent, transmit, False, **kwargs)
        self.notifs.append(order.clone())  # Уведомляем брокера о принятии/отклонении зявки на бирже
        return order

    def cancel(self, order):
        """Отмена заявки"""
        return self.cancel_order(order)

    def get_notification(self):
        if not self.notifs:  # Если в списке уведомлений ничего нет
            return None  # то ничего и возвращаем, выходим, дальше не продолжаем
        return self.notifs.popleft()  # Удаляем и возвращаем крайний левый элемент списка уведомлений

    def next(self):
        self.notifs.append(None)  # Добавляем в список уведомлений пустой элемент

    def stop(self):
        super(FinamBroker, self).stop()
        self.provider.unsubscribe_order_trade(self.order_trade_request_id)  # Отменяем подписки на зявки/сделки
        self.provider.on_order = self.provider.default_handler  # Обработка заявок
        # self.store.BrokerCls = None  # Удаляем класс брокера из хранилища

    # Функции

    def get_all_active_positions(self):
        """Все активные позиции по счету"""
        response = self.provider.get_portfolio(self.client_id)  # Портфель по счету
        if response:
            for position in response.positions:  # Пробегаемся по всем активным позициям счета
                si = next(item for item in self.provider.symbols.securities if item.market == position.market and item.code == position.security_code)  # Поиск тикера по рынку
                cross_rate = next(item.cross_rate for item in response.currencies if item.name == position.currency)  # Кол-во рублей за единицу валюты
                price = position.average_price * cross_rate
                dataname = self.provider.board_symbol_to_dataname(si.board, si.code)  # Название тикера
                self.positions[dataname] = Position(position.balance, price)  # Сохраняем в списке открытых позиций

    def get_order(self, transaction_id) -> Union[Order, None]:
        """Заявка BackTrader по номеру транзакции

        :param int transaction_id: Номер транзакции
        :return: Заявка BackTrader или None
        """
        for order in self.orders.values():  # Пробегаемся по всем заявкам на бирже
            if order.info['transaction_id'] == transaction_id:  # Если нашли совпадение по номеру транзакции
                return order  # то возвращаем заявку BackTrader
        return None  # иначе, ничего не найдено

    def create_order(self, owner, data, size, price=None, plimit=None, exectype=None, valid=None, oco=None, parent=None, transmit=True, simulated=False, is_buy=True, **kwargs):
        """Создание заявки. Привязка параметров счета и тикера. Обработка связанных и родительской/дочерних заявок"""
        use_credit = False
        if 'use_credit' in kwargs: use_credit = kwargs['use_credit']
        order = BuyOrder(owner=owner, data=data, size=size, price=price, pricelimit=plimit, exectype=exectype, valid=valid, oco=oco, parent=parent, simulated=simulated, transmit=transmit) if is_buy \
            else SellOrder(owner=owner, data=data, size=size, price=price, pricelimit=plimit, exectype=exectype, valid=valid, oco=oco, parent=parent, simulated=simulated, transmit=transmit)  # Заявка на покупку/продажу
        order.addcomminfo(self.getcommissioninfo(data))  # По тикеру выставляем комиссии в заявку. Нужно для исполнения заявки в BackTrader
        order.addinfo(**kwargs)  # Передаем в заявку все дополнительные свойства из брокера
        board, symbol = self.provider.dataname_to_board_symbol(data._name)  # По тикеру получаем код площадки и тикер
        order.addinfo(board=board, symbol=symbol)  # В заявку заносим код площадки board и тикер symbol
        if order.exectype in (Order.Close, Order.StopTrail, Order.StopTrailLimit, Order.Historical):  # Эти типы заявок не реализованы
            print(f'Постановка заявки {order.ref} по тикеру {board}.{symbol} отклонена. Работа с заявками {order.exectype} не реализована')
            order.reject(self)  # то отклоняем заявку
            self.oco_pc_check(order)  # Проверяем связанные и родительскую/дочерние заявки
            return order  # Возвращаем отклоненную заявку
        si = self.provider.get_symbol_info(board, symbol)  # Информация о тикере
        if not si:  # Если тикер не найден
            print(f'Постановка заявки {order.ref} по тикеру {board}.{symbol} отклонена. Тикер не найден')
            order.reject(self)  # то отклоняем заявку
            self.oco_pc_check(order)  # Проверяем связанные и родительскую/дочерние заявки
            return order  # Возвращаем отклоненную заявку
        if order.exectype != Order.Market and not order.price:  # Если цена заявки не указана для всех заявок, кроме рыночной
            price_type = 'Лимитная' if order.exectype == Order.Limit else 'Стоп'  # Для стоп заявок это будет триггерная (стоп) цена
            print(f'Постановка заявки {order.ref} по тикеру {board}.{symbol} отклонена. {price_type} цена (price) не указана для заявки типа {order.exectype}')
            order.reject(self)  # то отклоняем заявку
            self.oco_pc_check(order)  # Проверяем связанные и родительскую/дочерние заявки
            return order  # Возвращаем отклоненную заявку
        if order.exectype == Order.StopLimit and not order.pricelimit:  # Если лимитная цена не указана для стоп-лимитной заявки
            print(f'Постановка заявки {order.ref} по тикеру {board}.{symbol} отклонена. Лимитная цена (pricelimit) не указана для заявки типа {order.exectype}')
            order.reject(self)  # то отклоняем заявку
            self.oco_pc_check(order)  # Проверяем связанные и родительскую/дочерние заявки
            return order  # Возвращаем отклоненную заявку
        if oco:  # Если есть связанная заявка
            self.ocos[order.ref] = oco.ref  # то заносим в список связанных заявок
        if not transmit or parent:  # Для родительской/дочерних заявок
            parent_ref = getattr(order.parent, 'ref', order.ref)  # Номер транзакции родительской заявки или номер заявки, если родительской заявки нет
            if order.ref != parent_ref and parent_ref not in self.pcs:  # Если есть родительская заявка, но она не найдена в очереди родительских/дочерних заявок
                print(f'Постановка заявки {order.ref} по тикеру {board}.{symbol} отклонена. Родительская заявка не найдена')
                order.reject(self)  # то отклоняем заявку
                self.oco_pc_check(order)  # Проверяем связанные и родительскую/дочерние заявки
                return order  # Возвращаем отклоненную заявку
            pcs = self.pcs[parent_ref]  # В очередь к родительской заявке
            pcs.append(order)  # добавляем заявку (родительскую или дочернюю)
        if transmit:  # Если обычная заявка или последняя дочерняя заявка
            if not parent:  # Для обычных заявок
                return self.place_order(order, use_credit)  # Отправляем заявку на биржу
            else:  # Если последняя заявка в цепочке родительской/дочерних заявок
                self.notifs.append(order.clone())  # Удедомляем брокера о создании новой заявки
                return self.place_order(order.parent, use_credit)  # Отправляем родительскую заявку на биржу
        # Если не последняя заявка в цепочке родительской/дочерних заявок (transmit=False)
        return order  # то возвращаем созданную заявку со статусом Created. На биржу ее пока не ставим

    def place_order(self, order: Order, use_credit=False):
        """Отправка заявки на биржу"""
        buy_sell = BUY_SELL_BUY if order.isbuy() else BUY_SELL_SELL  # Покупка/продажа
        board = order.info['board']  # Код биржи
        symbol = order.info['symbol']  # Код тикера
        si = self.provider.get_symbol_info(board, symbol)  # Информация о тикере
        quantity = abs(order.size // si.lot_size)  # Размер позиции в лотах. В Финам всегда передается положительный размер лота
        if order.exectype == Order.Market:  # Рыночная заявка
            response = self.provider.new_order(self.client_id, board, symbol, buy_sell, quantity)
            order.addinfo(transaction_id=response.transaction_id)  # Идентификатор транзакции добавляем в заявку
        elif order.exectype == Order.Limit:  # Лимитная заявка
            response = self.provider.new_order(self.client_id, board, symbol, buy_sell, quantity, price=order.price, use_credit=use_credit)
            order.addinfo(transaction_id=response.transaction_id)  # Идентификатор транзакции добавляем в заявку
        elif order.exectype == Order.Stop:  # Стоп заявка
            response = self.provider.new_stop(self.client_id, board, symbol, buy_sell,
                                              StopLoss(activation_price=order.price, market_price=True,
                                                       quantity=StopQuantity(units=StopQuantityUnits.STOP_QUANTITY_UNITS_LOTS, value=quantity),
                                                       use_credit=False),
                                              valid_before=OrderValidBefore(type=OrderValidBeforeType.ORDER_VALID_BEFORE_TYPE_TILL_CANCELLED))
            order.addinfo(stop_id=response.stop_id)  # Идентификатор стоп заявки добавляем в заявку
        elif order.exectype == Order.StopLimit:  # Стоп-лимитная заявка
            response = self.provider.new_stop(self.client_id, board, symbol, buy_sell, None,
                                              StopLoss(activation_price=order.price, market_price=False, price=order.pricelimit,
                                                       quantity=StopQuantity(units=StopQuantityUnits.STOP_QUANTITY_UNITS_LOTS, value=quantity),
                                                       use_credit=False),
                                              valid_before=OrderValidBefore(type=OrderValidBeforeType.ORDER_VALID_BEFORE_TYPE_TILL_CANCELLED))
            order.addinfo(stop_id=response.stop_id)  # Идентификатор стоп заявки добавляем в заявку
        order.submit(self)  # Отправляем заявку на биржу (Order.Submitted)
        self.notifs.append(order.clone())  # Уведомляем брокера об отправке заявки на биржу
        order.accept(self)  # Заявка принята на бирже (Order.Accepted)
        self.orders[order.ref] = order  # Сохраняем заявку в списке заявок, отправленных на биржу
        return order  # Возвращаем заявку

    def cancel_order(self, order):
        """Отмена заявки"""
        if not order.alive():  # Если заявка уже была завершена
            return  # то выходим, дальше не продолжаем
        if order.exectype in (Order.Market, Order.Limit):  # Для рыночных и лимитных заявок
            self.provider.cancel_order(self.client_id, order.info['transaction_id'])  # Отмена активной заявки
        else:  # Для стоп заявок
            self.provider.cancel_stop(self.client_id, order.info['stop_id'])  # Отмена активной стоп заявки
        return order  # В список уведомлений ничего не добавляем. Ждем события on_order

    def oco_pc_check(self, order):
        """
        Проверка связанных заявок
        Проверка родительской/дочерних заявок
        """
        ocos = self.ocos.copy()  # Пока ищем связанные заявки, они могут измениться. Поэтому, работаем с копией
        for order_ref, oco_ref in ocos.items():  # Пробегаемся по списку связанных заявок
            if oco_ref == order.ref:  # Если в заявке номер эта заявка указана как связанная (по номеру транзакции)
                self.cancel_order(self.orders[order_ref])  # то отменяем заявку
        if order.ref in ocos.keys():  # Если у этой заявки указана связанная заявка
            oco_ref = ocos[order.ref]  # то получаем номер транзакции связанной заявки
            self.cancel_order(self.orders[oco_ref])  # отменяем связанную заявку

        if not order.parent and not order.transmit and order.status == Order.Completed:  # Если исполнена родительская заявка
            pcs = self.pcs[order.ref]  # Получаем очередь родительской/дочерних заявок
            for child in pcs:  # Пробегаемся по всем заявкам
                if child.parent:  # Пропускаем первую (родительскую) заявку
                    self.place_order(child)  # Отправляем дочернюю заявку на биржу
        elif order.parent:  # Если исполнена/отменена дочерняя заявка
            pcs = self.pcs[order.parent.ref]  # Получаем очередь родительской/дочерних заявок
            for child in pcs:  # Пробегаемся по всем заявкам
                if child.parent and child.ref != order.ref:  # Пропускаем первую (родительскую) заявку и исполненную заявку
                    self.cancel_order(child)  # Отменяем дочернюю заявку

    def on_order(self, event: OrderEvent):
        """Обработка заявок"""
        order: Order = self.get_order(event.transaction_id)  # Пытаемся получить заявку по номеру транзакции
        if not order:  # Если заявки нет в BackTrader (не из автоторговли)
            return  # то выходим, дальше не продолжаем
        status = event.status  # Статус заявки
        if status == OrderStatus.ORDER_STATUS_NONE:  # Если заявка не выставлена
            order.reject(self)  # то отклоняем заявку
            self.oco_pc_check(order)  # Проверяем связанные и родительскую/дочерние заявки
            return order  # Возвращаем отклоненную заявку
        elif status == OrderStatus.ORDER_STATUS_ACTIVE:  # Если заявка выставлена
            pass  # то ничего не делаем, т.к. уведомили о выставлении заявки на этапе ее постановки
        elif status == OrderStatus.ORDER_STATUS_CANCELLED:  # Если заявка отменена
            order.cancel()  # Отменяем существующую заявку
            self.notifs.append(order.clone())  # Уведомляем брокера об отмене заявки
            self.oco_pc_check(order)  # Проверяем связанные и родительскую/дочерние заявки (Canceled)
        elif status == OrderStatus.ORDER_STATUS_MATCHED:  # Если заявка исполнена
            dt = self.provider.utc_to_msk_datetime(datetime.now())  # Перевод текущего времени (другого нет) в московское
            pos = self.getposition(order.data)  # Получаем позицию по тикеру или нулевую позицию если тикера в списке позиций нет
            board = order.info['board']  # Код биржи
            symbol = order.info['symbol']  # Код тикера
            si = self.provider.get_symbol_info(board, symbol)  # Информация о тикере
            size = event.quantity * si.lot_size  # Кол-во в штуках
            if event.buy_sell == BUY_SELL_SELL:  # Если сделка на продажу
                size *= -1  # то кол-во ставим отрицательным
            price = event.price  # Цена исполнения за штуку
            psize, pprice, opened, closed = pos.update(size, price)  # Обновляем размер/цену позиции на размер/цену сделки
            order.execute(dt, size, price, closed, 0, 0, opened, 0, 0, 0, 0, psize, pprice)  # Исполняем заявку в BackTrader
            if order.executed.remsize:  # Если осталось что-то к исполнению
                if order.status != order.Partial:  # Если заявка переходит в статус частичного исполнения (может исполняться несколькими частями)
                    order.partial()  # то заявка частично исполнена
                    self.notifs.append(order.clone())  # Уведомляем брокера о частичном исполнении заявки
            else:  # Если ничего нет к исполнению
                order.completed()  # то заявка полностью исполнена
                self.notifs.append(order.clone())  # Уведомляем брокера о полном исполнении заявки
                # Снимаем oco-заявку только после полного исполнения заявки
                # Если нужно снять oco-заявку на частичном исполнении, то прописываем это правило в ТС
                self.oco_pc_check(order)  # Проверяем связанные и родительскую/дочерние заявки (Completed)
