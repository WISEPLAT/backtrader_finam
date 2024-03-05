import ast
from datetime import datetime, timedelta
from backtrader.dataseries import TimeFrame

from .finam_broker import FinamBroker
from .finam_feed import FinamData

from FinamPy import FinamPy
from FinamPy.proto.tradeapi.v1.candles_pb2 import DayCandleTimeFrame, IntradayCandleTimeFrame
from google.protobuf.json_format import MessageToJson, Parse  # Будем хранить справочник в файле в формате JSON


class FinamStore(object):
    """Класс получения данных по тикеру"""
    _GRANULARITIES = {  # Все временнЫе интервалы
        (TimeFrame.Minutes, 1): (IntradayCandleTimeFrame.INTRADAYCANDLE_TIMEFRAME_M1, "M1"),
        (TimeFrame.Minutes, 5): (IntradayCandleTimeFrame.INTRADAYCANDLE_TIMEFRAME_M5, "M5"),
        (TimeFrame.Minutes, 10): (IntradayCandleTimeFrame.INTRADAYCANDLE_TIMEFRAME_M5, "M10"),  # need to resample
        (TimeFrame.Minutes, 15): (IntradayCandleTimeFrame.INTRADAYCANDLE_TIMEFRAME_M15, "M15"),
        (TimeFrame.Minutes, 30): (IntradayCandleTimeFrame.INTRADAYCANDLE_TIMEFRAME_M15, "M30"),  # need to resample
        (TimeFrame.Minutes, 60): (IntradayCandleTimeFrame.INTRADAYCANDLE_TIMEFRAME_H1, "H1"),
        (TimeFrame.Days, 1): (DayCandleTimeFrame.DAYCANDLE_TIMEFRAME_D1, "D1"),
        (TimeFrame.Weeks, 1): (DayCandleTimeFrame.DAYCANDLE_TIMEFRAME_W1, "W1"),
    }

    def __init__(self, client_id, access_token, max_errors_requests_per_ticker=2, **kwargs):
        """Инициализация необходимых переменных"""

        self.client_id = client_id
        print("Авторизуемся на Finam")
        self.fp_provider = FinamPy(client_id, access_token)

        self._cash = 0
        self._value = 0

        self._broker = FinamBroker(store=self)
        self._data = None
        self._datas = {}
        self._all_securities = {}

        # limits of Finam requests
        # ВНИМАНИЕ! Есть ограничение по кол-ву запросов в минуту!!!! https://finamweb.github.io/trade-api-docs/limits
        # Таблица лимитов
        # Сервис	Количество запросов в минуту
        # securities	1
        # portfolio	100
        # orders/stops	100
        # candles	120
        self.max_requests = 120  # Максимальное кол-во запросов в минуту
        self.requests = 0  # Выполненное кол-во запросов в минуту
        self.next_run = datetime.now() + timedelta(minutes=1, seconds=3)  # Время следующего запуска запросов

        self.max_errors_requests_per_ticker = max_errors_requests_per_ticker  # при превышении этого значения, будет прекращена попытка получить данные  # -1 == бесконечно пытаться получить данные

    def getbroker(self, use_positions=True):
        self._broker.p.use_positions = use_positions
        self._broker.get_all_active_positions()
        return self._broker

    def getdata(self, **kwargs):  # timeframe, compression, from_date=None, live_bars=True
        """Метод получения исторических и live данных по тикеру"""
        ticker = kwargs['dataname']
        compression = 1
        if 'compression' in kwargs: compression = kwargs['compression']
        tf, tf_txt = self.get_interval(kwargs['timeframe'], compression)
        if ticker not in self._datas:
            self._datas[f"{ticker}_{tf_txt}"] = FinamData(store=self, **kwargs)  # timeframe=timeframe, compression=compression, from_date=from_date, live_bars=live_bars
        return self._datas[f"{ticker}_{tf_txt}"]

    def get_interval(self, timeframe, compression):
        """Метод получения ТФ по тикеру для finam из ТФ backtrader"""
        _tf = self._GRANULARITIES.get((timeframe, compression))
        return _tf[0], _tf[1]

    def get_symbol_info(self, board, symbol):
        """Метод получения информации по тикеру"""
        # return self.fp_provider.get_symbol_info(board, symbol)
        securities = ast.literal_eval(MessageToJson(self.fp_provider.symbols))  # превращаем в словарь
        # # for sec_info in securities["securities"]: all_securities[sec_info["code"]] = sec_info
        for sec_info in securities["securities"]:
            self._all_securities[f'{sec_info["board"]}.{sec_info["code"]}'] = sec_info
        return self._all_securities[f"{board}.{symbol}"]
