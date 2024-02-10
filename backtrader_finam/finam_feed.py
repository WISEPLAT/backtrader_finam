from collections import deque
from datetime import datetime, timezone, timedelta, time
from time import sleep

import pandas as pd

from backtrader.feed import DataBase
from backtrader.utils import date2num

from backtrader import TimeFrame as tf
from FinamPy.proto.tradeapi.v1.candles_pb2 import DayCandleInterval, IntradayCandleInterval
from google.type.date_pb2 import Date
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.json_format import MessageToDict


class FinamData(DataBase):
    """Класс получения исторических и live данных по тикеру"""
    params = (
        ('drop_newest', False),
    )
    
    # States for the Finite State Machine in _load
    _ST_LIVE, _ST_HISTORBACK, _ST_OVER = range(3)

    def __init__(self, store, **kwargs):  # def __init__(self, store, timeframe, compression, from_date, live_bars):
        """Инициализация необходимых переменных"""
        self.interval = None
        self.timeframe_txt = None
        self.timeframe = tf.Minutes
        self.compression = 1
        self.from_date = None
        self.live_bars = None

        self._state = None

        self.get_live_bars_from = None  # с какой даты получаем live бары

        self.ticker = self.p.dataname
        _point = self.ticker.index('.')
        self.board = self.ticker[0:_point]  # Класс тикера
        self.symbol = self.ticker[_point + 1:]  # Тикер +1 для точки

        if hasattr(self.p, 'timeframe'): self.timeframe = self.p.timeframe
        if hasattr(self.p, 'compression'): self.compression = self.p.compression
        if hasattr(self.p, 'fromdate'): self.from_date = datetime.combine(self.p.fromdate, time.min)

        if 'live_bars' in kwargs: self.live_bars = kwargs['live_bars']

        self._store = store
        self._data = deque()

        self.all_history_data = None  # Вся история по тикеру
        self.all_ohlc_data = []  # Вся история по тикеру
        self.ticker_has_error = False  # Есть ли ошибка при получении истории тикера
        # print("Ok", self.timeframe, self.compression, self.from_date, self._store, self.live_bars, self.board, self.symbol)

    def _load(self):
        """Метод загрузки"""
        if self._state == self._ST_OVER:
            return False
        elif self._state == self._ST_LIVE:
            # return self._load_kline()
            if self._load_kline():
                return True
            else:
                self._start_live()
        elif self._state == self._ST_HISTORBACK:
            if self._load_kline():
                return True
            else:
                self._start_live()

    def _load_kline(self):
        """Обработка одной строки данных"""
        try:
            kline = self._data.popleft()
        except IndexError:
            return None

        if type(kline) == list:
            timestamp, open_, high, low, close, volume = kline
            self.lines.datetime[0] = date2num(timestamp)
            self.lines.open[0] = open_
            self.lines.high[0] = high
            self.lines.low[0] = low
            self.lines.close[0] = close
            self.lines.volume[0] = volume

        return True

    def _start_live(self):
        """Получение live данных"""
        while True:
            if self.live_bars:

                if self._state != self._ST_LIVE:
                    print(f"Live started for ticker: {self.ticker}")
                    self._state = self._ST_LIVE
                    self.put_notification(self.LIVE)

                if not self.get_live_bars_from:
                    # self.get_live_bars_from = datetime.now().date()
                    self.get_live_bars_from = datetime.combine(datetime.now().date(), time.min)
                else:
                    # self.get_live_bars_from = self.get_live_bars_from.date()
                    self.get_live_bars_from = datetime.combine(self.get_live_bars_from.date(), time.min)

                klines, get_live_bars_from = self.get_candles(from_date=self.get_live_bars_from,
                                                                  board=self.board,
                                                                  symbol=self.symbol,
                                                                  interval=self.interval,
                                                                  timeframe_txt=self.timeframe_txt, is_live_request=True)

                if not klines.empty:  # если есть, что обрабатывать
                    new_klines = klines.values.tolist()  # берем новые строки данных
                    _empty = True
                    _klines = []
                    for kline in new_klines:
                        if kline not in self.all_history_data:  # если такой строки данных нет,
                            self.all_history_data.append(kline)
                            _klines.append(kline)
                            _empty = False
                    self._data.extend(_klines)  # отправляем в обработку
                    if _klines or _empty:  # если получили новые данные
                        break

                # здесь можно оптимизировать через потоки и запрашивать не так часто, пересчитывая сколько ждать
                sleep(1)

            else:
                self._state = self._ST_OVER
                break

    def haslivedata(self):
        return self._state == self._ST_LIVE and self._data

    def islive(self):
        return True

    def start(self):  # "start" => "_load
        """Получение исторических данных"""
        DataBase.start(self)

        # если ТФ задан не корректно, то ничего не делаем
        self.interval, self.timeframe_txt = self._store.get_interval(self.timeframe, self.compression)
        if self.interval is None:
            self._state = self._ST_OVER
            self.put_notification(self.NOTSUPPORTED_TF)
            return

        # если не можем получить данные по тикеру, то ничего не делаем
        self.symbol_info = self._store.get_symbol_info(self.board, self.symbol)
        if self.symbol_info is None:
            self._state = self._ST_OVER
            self.put_notification(self.NOTSUBSCRIBED)
            return

        # получение исторических данных
        if self.from_date:
            self._state = self._ST_HISTORBACK
            self.put_notification(self.DELAYED)  # Отправляем уведомление об отправке исторических (не новых) баров

            klines, get_live_bars_from = self.get_candles(from_date=self.from_date,
                                                              board=self.board,
                                                              symbol=self.symbol,
                                                              interval=self.interval,
                                                              timeframe_txt=self.timeframe_txt, is_live_request=False)  # , is_test=True

            if not klines.empty:  # если есть, что обрабатывать
                self.get_live_bars_from = get_live_bars_from

                print(f"- {self.ticker} - History data - Ok")

                klines = klines.values.tolist()
                self.all_history_data = klines  # при первом получении истории - её всю записываем в виде list

                try:
                    if self.p.drop_newest:
                        klines.pop()
                    self._data.extend(klines)
                except Exception as e:
                    print("Exception (try set from_date in utc format):", e)
            else:
                print(f"- {self.ticker} - History data - False")

        else:
            self._start_live()

    def get_previous_future_candle_time(self, timeframe):
        # timeframe = "D1"
        now = datetime.now()
        # now = datetime.datetime.fromisoformat("2023-03-20 00:00")
        now_hour = now.hour
        now_minutes = now.minute

        _previous_candle_time, _current_candle_time, _future_candle_time = None, None, None

        if timeframe == "D1":
            _current_candle_time = datetime.fromisoformat(now.strftime('%Y-%m-%d') + " " + "00:00")
            # print(_current_candle_time)

            # get day of week as an integer
            day_of_week = _current_candle_time.weekday()
            # print('Day of a week is:', day_of_week)

            days_back = 1
            if day_of_week == 0: days_back = 3  # если сегодня понедельник, то смещение на пятницу - праздничные дни не учитываем

            _previous_candle_time = _current_candle_time - timedelta(days=days_back)
            _future_candle_time = _current_candle_time + timedelta(days=days_back)
            # print(_previous_candle_time)

        if timeframe in ['H4', 'H1', 'M30', 'M15', 'M10', 'M5', 'M1']:
            timeframe_to_minutes = {'H4': 240, 'H1': 60, 'M30': 30, 'M15': 15, 'M10': 10, 'M5': 5, 'M1': 1}
            _minutes = timeframe_to_minutes[timeframe]

            # H1 .. M1
            now_minutes = (now_minutes // _minutes) * _minutes
            pre_minutes = (now_minutes // _minutes + 1) * _minutes - now_minutes

            _current_candle_time = datetime.fromisoformat(
                now.strftime('%Y-%m-%d') + " " + f"{now_hour:02}:{now_minutes:02}")
            # print(_current_candle_time)

            _previous_candle_time = _current_candle_time - timedelta(minutes=pre_minutes)
            _future_candle_time = _current_candle_time + timedelta(minutes=pre_minutes)
            # print(_previous_candle_time)

        return _previous_candle_time, _current_candle_time, _future_candle_time

    def get_candles(self, from_date, board, symbol, interval, timeframe_txt, is_test=False, is_live_request=False):
        """Получение баров, используем библиотеку moexalgo
            :param date from_date: С какой даты получаем данные
            :param str board: Площадка тикера
            :param str symbol: Код тикера
            :param str interval: Временной интервал 'M1', 'M5', 'M15', 'H1', 'D1', '1W' + resampling for 'M10', 'M30'
            :param str timeframe_txt: Временной интервал в txt
            :param bool is_test: Для теста / debug
            :param bool is_live_request: Вызов функции для получения live / history данных
        """

        # проверяем, нужно ли делать resample
        resample = False
        interval_to = None
        if timeframe_txt == 'M10':
            resample = True
            interval_to = '10T'  # is equal for '10M (pandas)

        if timeframe_txt == 'M30':
            resample = True
            interval_to = '30T'  # is equal for 'M30 (pandas)

        time_frame = interval
        next_bar_open_utc = from_date.replace(tzinfo=timezone.utc)

        intraday = True
        if timeframe_txt in ["D1", "W1", "MN1"]: intraday = False

        get_live_bars_from = None
        _previous_candle_time, _current_candle_time, _future_candle_time = self.get_previous_future_candle_time(timeframe=timeframe_txt)

        interval_ = IntradayCandleInterval(count=500) if intraday else DayCandleInterval(count=500)  # Нужно поставить максимальное кол-во баров. Максимум, можно поставить 500
        from_ = getattr(interval_, 'from')  # Т.к. from - ключевое слово в Python, то получаем атрибут from из атрибута интервала
        # to_ = getattr(interval_, 'to')  # Аналогично будем работать с атрибутом to для единообразия

        last_dt = from_date
        df = pd.DataFrame()

        max_errors_requests_per_ticker = self._store.max_errors_requests_per_ticker  # при превышении этого значения, будет прекращена попытка получить данные  # -1 == бесконечно пытаться получить данные

        while True:  # Будем получать данные пока не получим все

            if intraday:  # Для интрадея datetime -> Timestamp
                from_.seconds = Timestamp(seconds=int(next_bar_open_utc.timestamp())).seconds  # Дата и время начала интервала UTC
            else:  # Для дневных интервалов и выше datetime -> Date
                date_from = Date(year=next_bar_open_utc.year, month=next_bar_open_utc.month, day=next_bar_open_utc.day)  # Дата начала интервала UTC
                from_.year = date_from.year
                from_.month = date_from.month
                from_.day = date_from.day

            if self._store.requests >= self._store.max_requests:  # Если достигли допустимого кол-ва запросов в минуту
                sleep_seconds = (self._store.next_run - datetime.now()).total_seconds()  # Время ожидания 1 минута с первого запроса
                if sleep_seconds < 0: sleep_seconds = abs(60 - abs(sleep_seconds))  # fix minus time
                print('Достигнут предел', self._store.max_requests, 'запросов в минуту. Ждем', sleep_seconds, 'с до следующей группы запросов...')
                for i in range(int(sleep_seconds) + 2):
                    print(f"{int(sleep_seconds - i)}", end=" ")
                    sleep(1)
                print()
                # sleep(sleep_seconds)  # Ждем минуту с первого запроса
                self._store.requests = 0  # Сбрасываем выполненное кол-во запросов в минуту
            if self._store.requests == 0:  # Если первый запрос в минуту
                self._store.next_run = datetime.now() + timedelta(minutes=1, seconds=3)  # Следующую группу запросов сможем запустить не ранее, чем через 1 минуту
            self._store.requests += 1  # Следующий запрос
            # print(self._store.requests, self.ticker)
            # print('Запрос', self._store.requests, 'с', next_bar_open_utc, 'по', todate_min_utc, "live:", is_live_request)

            new_bars_dict = []  # Будем получать историю
            try:  # При запросе истории Финам может выдать ошибку
                new_bars_dict = MessageToDict(self._store.fp_provider.get_intraday_candles(board, symbol, time_frame, interval_) if intraday
                    else self._store.fp_provider.get_day_candles(board, symbol, time_frame, interval_), including_default_value_fields=True)['candles']  # Получаем бары, переводим в словарь/список
            except Exception as e:  # Если получили ошибку
                print(f'Ошибка при получении истории (history) {self.ticker}: {e}')  # то выводим ее в консоль
                print(f'Скорее всего превысили max_requests candles 120, ждемс...')
                sleep_seconds = 60
                for i in range(int(sleep_seconds) + 2):
                    print(f"{int(sleep_seconds - i)}", end=" ")
                    sleep(1)
                print()
                self._store.requests = 1  # Сбрасываем выполненное кол-во запросов в минуту +1
                self._store.next_run = datetime.now() + timedelta(minutes=1, seconds=3)  # Следующую группу запросов сможем запустить не ранее, чем через 1 минуту
                if max_errors_requests_per_ticker == -1:
                    continue  # заново выполнить запрос, если была ошибка  # -1 == бесконечно пытаться получить данные
                if max_errors_requests_per_ticker > 0:
                    max_errors_requests_per_ticker -= 1
                    continue  # заново выполнить запрос, если была ошибка
                if max_errors_requests_per_ticker == 0:  # если не получили истории по тикеру, то с тикером некая ошибка
                    self.ticker_has_error = True


            _previous_candle_time, _current_candle_time, _future_candle_time = self.get_previous_future_candle_time(timeframe=timeframe_txt)

            new_bars_list = []  # Список новых бар
            new_ohlc_rows = []  # Список новых бар
            added_new_row = False

            if len(new_bars_dict):  # Если пришли новые бары
                first_bar_open_dt = self._store.fp_provider.utc_to_msk_datetime(datetime.fromisoformat(new_bars_dict[0]['timestamp'][:-1])) if intraday else \
                    datetime(new_bars_dict[0]['date']['year'], new_bars_dict[0]['date']['month'], new_bars_dict[0]['date']['day'])  # Дату и время первого полученного бара переводим из UTC в МСК
                last_bar_open_dt = self._store.fp_provider.utc_to_msk_datetime(datetime.fromisoformat(new_bars_dict[-1]['timestamp'][:-1])) if intraday else \
                    datetime(new_bars_dict[-1]['date']['year'], new_bars_dict[-1]['date']['month'], new_bars_dict[-1]['date']['day'])  # Дату и время последнего полученного бара переводим из UTC в МСК

                for new_bar in new_bars_dict:  # Пробегаемся по всем полученным барам
                    # Дату/время UTC получаем в формате ISO 8601. Пример: 2023-06-16T20:01:00Z
                    # В статье https://stackoverflow.com/questions/127803/how-do-i-parse-an-iso-8601-formatted-date описывается проблема, что Z на конце нужно убирать
                    dt = self._store.fp_provider.utc_to_msk_datetime(datetime.fromisoformat(new_bar['timestamp'][:-1])) if intraday else \
                        datetime(new_bar['date']['year'], new_bar['date']['month'], new_bar['date']['day'])  # Дату и время переводим из UTC в МСК
                    open_ = round(int(new_bar['open']['num']) * 10 ** -int(new_bar['open']['scale']), int(new_bar['open']['scale']))
                    high = round(int(new_bar['high']['num']) * 10 ** -int(new_bar['high']['scale']), int(new_bar['high']['scale']))
                    low = round(int(new_bar['low']['num']) * 10 ** -int(new_bar['low']['scale']), int(new_bar['low']['scale']))
                    close = round(int(new_bar['close']['num']) * 10 ** -int(new_bar['close']['scale']), int(new_bar['close']['scale']))
                    volume = int(new_bar['volume'])

                    if dt < _current_candle_time and not is_live_request:  # текущий формируемый бар нам не нужен!!! - для запроса исторических данных
                        new_bars_list.append({'datetime': dt, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume})

                    if dt <= _previous_candle_time and is_live_request:  # текущий формируемый бар нам не нужен!!! - для live сравниваем с другим числом!!!
                        new_bars_list.append({'datetime': dt, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume})
                        # print(get_live_bars_from, _previous_candle_time, _current_candle_time, _future_candle_time)

                    row = {'datetime': dt, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume}
                    if dt not in self.all_ohlc_data and dt <= _previous_candle_time and row not in new_ohlc_rows:
                        new_ohlc_rows.append(row)
                        self.all_ohlc_data.append(dt)
                        added_new_row = True

                if added_new_row:
                    stats = pd.DataFrame(new_ohlc_rows)  # Из списка создаем pandas DataFrame
                    last_stats_dt = stats.iloc[-1]['datetime']  # Последняя полученная дата и время
                    last_stats_date = last_stats_dt.date()  # Последняя полученная дата

                    df = pd.concat([df, stats]).drop_duplicates(keep='last')  # Добавляем новые данные в существующие. Удаляем дубликаты. Сбрасываем индекс
                    if not is_live_request:
                        print(f'- {self.ticker} - Получены бары с', first_bar_open_dt, 'по', last_bar_open_dt, "live:", is_live_request)
                        # print("\t - ", last_stats_dt, last_dt, type(last_stats_dt), type(last_dt), last_stats_dt == last_dt)

                    if last_stats_dt == last_dt:  # Если не получили новые значения
                        # print(self.symbol, '- Все данные получены 1')
                        get_live_bars_from = last_stats_dt
                        break  # то дальше не продолжаем

                    last_dt = last_stats_dt  # Запоминаем последние полученные дату и время
                    last_date = last_stats_date  # и дату

                    next_bar_open_utc = last_bar_open_dt  # last_stats_dt

            if not added_new_row:  # and not is_live_request:
                break

        # если требуется сделать resample
        if resample and not df.empty:
            ohlc_dict = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum',
                # 'value': 'sum',
            }
            df.set_index('datetime', inplace=True)
            df.index = pd.to_datetime(df.index, format='%Y-%m-%d %H:%M:%S')  # Переводим индекс в формат datetime
            df_res = df.resample(interval_to).agg(ohlc_dict)
            df_res = df_res[df_res['open'].notna()]  # just take the rows where 'open' is not NA
            df_res.reset_index(inplace=True)
            df = df_res.copy()

        # test for live in offline
        if is_test:
            df.drop(df.tail(4).index,inplace=True) # drop last n rows
            get_live_bars_from = df.iloc[-1]['datetime']
            return df, get_live_bars_from

        return df, get_live_bars_from
