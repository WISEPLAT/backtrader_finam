# backtrader_finam

Интеграция API Finam с [Backtrader](https://github.com/WISEPLAT/backtrader ).

С помощью этой интеграции вы можете делать:
- Тестирование вашей стратегии на исторических данных с Финама
- Запускать торговые системы в Live для автоматической/алгоритмической торговли через брокера Финам
- Загружать live / исторические данные по акциям, фьючерсам и иностранным инструментам
- Создавать и тестировать свои торговые стратегии пользуясь возможностями библиотеки [Backtrader](https://github.com/WISEPLAT/backtrader )
  - Много полезной документации о том, как делать стратегии есть [здесь](https://www.backtrader.com/docu/quickstart/quickstart/ ).

Для подключения к API мы используем библиотеки [backtrader_finam](https://github.com/WISEPLAT/backtrader_finam ) + [Backtrader](https://github.com/WISEPLAT/backtrader ) + [FinamPy](https://github.com/WISEPLAT/FinamPy ).

## Установка
1) Самый простой способ:
```shell
pip install backtrader_finam
```
или
```shell
git clone https://github.com/WISEPLAT/backtrader_finam
```
или
```shell
pip install git+https://github.com/WISEPLAT/backtrader_finam.git
```

2) Пожалуйста, используйте backtrader из моего репозитория (так как вы можете размещать в нем свои коммиты). Установите его:
```shell
pip install git+https://github.com/WISEPLAT/backtrader.git
```
-- Могу ли я использовать вашу интеграцию с оригинальным backtrader?

-- Да, вы можете использовать оригинальный backtrader, так как автор оригинального backtrader одобрил все мои изменения.

Вот ссылка: [mementum/backtrader#472](https://github.com/mementum/backtrader/pull/472)

3) У нас есть некоторые зависимости, вам нужно их установить:
```shell
pip install pytz requests grpcio protobuf types-protobuf googleapis-common-protos numpy pandas backtrader requests websockets matplotlib
```
Обязательно! Выполните в корне вашего проекта через терминал эту команду (для избежания ошибки: **ModuleNotFoundError: No module named 'FinamPy'**):
```shell
git clone https://github.com/WISEPLAT/FinamPy
```
для клонирования библиотеки, которая позволяет работать с функционалом API брокера Финам.

### Начало работы
Чтобы было легче разобраться как всё работает, сделано множество примеров в папках **DataExamplesMoexAlgo_ru** и **StrategyExamplesMoexAlgo_ru**.

Перед запуском примера, необходимо получить свой API ключ и номер торгового счета, и прописать их в файле **my_config\Config_Finam.py:**

```python
# content of my_config\Config_Finam.py 
class Config:
    ClientIds = ('<Торговый счет>',)  # Торговые счёта
    AccessToken = '<Токен>'  # Торговый токен доступа
```

####  Как получить номер торгового счета и API ключ:
1. Открыть счет в "Финаме" https://open.finam.ru/registration
2. Зарегистрироваться в сервисе Comon https://www.comon.ru/
3. В личном кабинете Comon получить токен https://www.comon.ru/my/trade-api/tokens
4. Скопировать и вставить в файл **my_config\Config_Finam.py** полученные **"Ключ API"** и **"Номер счета"**

#### Теперь можно запускать примеры

В папке **DataExamplesFinam_ru** находится код примеров по работе с биржевыми данными через API интерфейс.

* **01 - Symbol.py** - торговая стратегия для получения исторических и "живых" данных одного тикера по одному таймфрейму
* **02 - Symbol data to DF.py** - экспорт в csv файл исторических данных одного тикера по одному таймфрейму
* **03 - Symbols.py** - торговая стратегия для нескольких тикеров по одному таймфрейму
* **04 - Rollover.py** - запуск торговой стратегии на склейке данных из файла с историческими данными и последней загруженной истории с брокера
* **05 - Timeframes.py** - торговая стратегия для одного тикера по разным таймфреймам
* **Strategy.py** - Пример торговой стратегии, которая только выводит данные по тикеру/тикерам OHLCV

В папке **StrategyExamplesFinam_ru** находится код примеров стратегий.  

* **01 - Live Trade - broker Finam.py** - Пример торговой стратегии в live режиме для тикера SBER - брокер Финам. 
  * Пример выставления заявок на биржу через брокера Финам и их снятие.
    * Пожалуйста, имейте в виду! Это live режим - если на рынке произойдет значительное изменение цены в сторону понижения более чем на 0.5% - ордер может быть выполнен.... 
    * **Не забудьте после теста снять с биржи выставленные заявки!**


* **02 - Live Trade - LimitCancel.py** - Пример торговой стратегии в live режиме для тикера SBER - брокер Финам. 
  * Пример выставления заявок на биржу через брокера Финам и их снятие.
    * Пожалуйста, имейте в виду! Это live режим - если на рынке произойдет значительное изменение цены в сторону понижения более чем на 0.5% - ордер может быть выполнен.... 
    * **Не забудьте после теста снять с биржи выставленные заявки!**


* **03 - Offline Backtest.py** - Пример торговой стратегии для теста на истории - не live режим - для двух тикеров SBER и LKOH.
  * В стратегии показано как применять индикаторы (SMA, RSI) к нескольким тикерам одновременно.
    * Не live режим - для тестирования стратегий без отправки заявок на биржу!


* **04 - Offline Backtest MultiPortfolio.py** - Пример торговой стратегии для теста на истории - не live режим - для множества тикеров, которые можно передавать в стратегию списком (SBER, LKOH, AFLT, GMKN). 
  * В стратегии показано как применять индикаторы (SMA, RSI) к нескольким тикерам одновременно.
    * Не live режим - для тестирования стратегий без отправки заявок на биржу!


* **05 - Offline Backtest Indicators.py** - Пример торговой стратегии для теста на истории с использованием индикаторов SMA и RSI - не live режим - для двух тикеров SBER и LKOH. 
  * В стратегии показано как применять индикаторы (SMA, RSI) к нескольким тикерам одновременно.
    * генерит 177% дохода на момент записи видео )) 
    * Не live режим - для тестирования стратегий без отправки заявок на биржу!


* **06 - Offline Backtest - Just Print OHLCV with check on Failed Tickers.py**
  * Стратегия просто выводит OHLCV, исключая Тикеры по которым не смогли получить исторические данные.

## Спасибо
- Команде разработчиков Backtrader: очень простая и классная библиотека!
- Команде [разработчиков FinamPy](https://github.com/cia76): за превосходные бесплатные библиотеки для live торговли реализующие подключения к брокерам 

## Важно
Исправление ошибок, доработка и развитие библиотеки осуществляется автором и сообществом!

**Пушьте ваши коммиты!** 

# Условия использования
Библиотека backtrader_finam позволяющая делать интеграцию Backtrader и MOEX API - это **Программа** созданная исключительно для удобства работы.
При использовании **Программы** Пользователь обязан соблюдать положения действующего законодательства Российской Федерации или своей страны.
Использование **Программы** предлагается по принципу «Как есть» («AS IS»). Никаких гарантий, как устных, так и письменных не прилагается и не предусматривается.
Автор и сообщество не дает гарантии, что все ошибки **Программы** были устранены, соответственно автор и сообщество не несет никакой ответственности за
последствия использования **Программы**, включая, но, не ограничиваясь любым ущербом оборудованию, компьютерам, мобильным устройствам, 
программному обеспечению Пользователя вызванным или связанным с использованием **Программы**, а также за любые финансовые потери,
понесенные Пользователем в результате использования **Программы**.
Никто не ответственен за потерю данных, убытки, ущерб, включаю случайный или косвенный, упущенную выгоду, потерю доходов или любые другие потери,
связанные с использованием **Программы**.

**Программа** распространяется на условиях лицензии [MIT](https://choosealicense.com/licenses/mit).

## История звезд
Пожалуйста, поставьте Звезду 🌟 этому коду

[![Star History Chart](https://api.star-history.com/svg?repos=WISEPLAT/backtrader_finam&type=Timeline)](https://star-history.com/#WISEPLAT/backtrader_finam&Timeline)

## Star History
Please, put a Star 🌟 for this code

==========================================================================


# backtrader_finam
Finam API integration with [Backtrader](https://github.com/WISEPLAT/backtrader).

With this integration you can do:
 - Backtesting your strategy on historical data from Finam 
 - Launch LIVE trading systems for automatic trading by broker Finam
 - Download live / historical data on stocks, futures and foreign instruments
- Create and test your trading strategies using the library's features [Backtrader](https://github.com/WISEPLAT/backtrader )
  - There is a lot of useful documentation on how to make strategies [(see here)](https://www.backtrader.com/docu/quickstart/quickstart/ ).

For API connection we are using libraries [backtrader_finam](https://github.com/WISEPLAT/backtrader_finam ) + [Backtrader](https://github.com/WISEPLAT/backtrader ) + [FinamPy](https://github.com/WISEPLAT/FinamPy ).

## Installation
1) The simplest way:
```shell
pip install backtrader_finam
```
or
```shell
git clone https://github.com/WISEPLAT/backtrader_finam
```
or
```shell
pip install git+https://github.com/WISEPLAT/backtrader_finam.git
```

2) Please use backtrader from my repository (as your can push your commits in it). Install it:
```shell
pip install git+https://github.com/WISEPLAT/backtrader.git
```
-- Can I use your integration library with original backtrader?

-- Yes, you can use original backtrader, as the author of original backtrader had approved all my changes. 

Here is the link: [mementum/backtrader#472](https://github.com/mementum/backtrader/pull/472)

3) We have some dependencies, you need to install them: 
```shell
pip install pytz requests grpcio protobuf types-protobuf googleapis-common-protos numpy pandas backtrader requests websockets matplotlib
```
Important! Run this command in the root of your project via the terminal (to prevent error: **ModuleNotFoundError: No module named 'FinamPy'**):
```shell
git clone https://github.com/WISEPLAT/FinamPy
```
to clone a library that allows you to work with the functionality of the Finam broker API.

### Getting started
To make it easier to figure out how everything works, many examples have been made in the folders **DataExamplesMoexAlgo** and **StrategyExamplesMoexAlgo**.

Before running the example, you need to get your API key and trading account number, and register them in the file **my_config\Config_Finam.py:**

```python
# content of my_config\Config_Finam.py 
class Config:
    ClientIds = ('<Trading account>',)  # Trading accounts
    AccessToken = '<Token>'  # Trade Access Token
```

#### How to get the trading account number and API key:
1. Open an account in Finam https://open.finam.ru/registration
2. Register in the Comon service https://www.comon.ru/
3. Get a token in your Comon personal account https://www.comon.ru/my/trade-api/tokens
4. Copy and paste to the file **my_config\Config_Finam.py** received **"API key"** and **"Account number"**

#### Now you can run the examples

The **DataExamplesMoexAlgo** folder contains the code of examples for working with exchange data via the [MOEX](https://www.moex.com/ru/algopack/about ) API.

* **01 - Symbol.py** - trading strategy for obtaining historical and "live" data of one ticker for one timeframe
* **02 - Symbol data to DF.py** - export to csv file of historical data of one ticker for one timeframe
* **03 - Symbols.py** - trading strategy for multiple tickers on the same timeframe
* **04 - Rollover.py** - launch of a trading strategy based on gluing data from a file with historical data and the last downloaded history from the broker
* **05 - Timeframes.py** - trading strategy is running on different timeframes.
* **Strategy.py** - An example of a trading strategy that only outputs data of the OHLCV for ticker/tickers

The **StrategyExamplesMoexAlgo** folder contains the code of sample strategies.

* **01 - Live Trade - broker Finam.py** - An example of a live trading strategy for SBER ticker - broker Finam.
  * Example of placing and cancel orders on the exchange with the use of broker Finam.
    * Please be aware! This is Live order - if market has a big change down in value of price more than 0.5% - the order will be completed.... 
    * **Do not forget to cancel the submitted orders from the exchange after the test!**


* **02 - Live Trade - LimitCancel.py** - An example of a live trading strategy for SBER ticker - broker Finam.
  * Example of placing and cancel orders on the exchange with the use of broker Finam.
    * Please be aware! This is Live order - if market has a big change down in value of price more than 0.5% - the order will be completed.... 
    * **Do not forget to cancel the submitted orders from the exchange after the test!**


* **03 - Offline Backtest.py** - An example of a trading strategy on a historical data - not live mode - for two SBER and LKOH tickers.
  * The strategy shows how to apply indicators (SMA, RSI) to several tickers at the same time.
    * Not a live mode - for testing strategies without sending orders to the exchange!


* **04 - Offline Backtest MultiPortfolio.py** - An example of a trading strategy on a historical data - not live mode - for a set of tickers that can be transferred to the strategy in a list (SBER, LKOH, AFLT, GMKN).
  * The strategy shows how to apply indicators (SMA, RSI) to several tickers at the same time.
    * Not a live mode - for testing strategies without sending orders to the exchange!


* **05 - Offline Backtest Indicators.py** - An example of a trading strategy for a history test using SMA and RSI indicators - not live mode - for two SBER and LKOH tickers.
  * The strategy shows how to apply indicators (SMA, RSI) to several tickers at the same time.
    * generates 177% of revenue at the time of video recording))
    * Non-live mode - for testing strategies without sending orders to the exchange!


* **06 - Offline Backtest - Just Print OHLCV with check on Failed Tickers.py**
  * The strategy simply outputs OHLCV, excluding Tickers for which historical data could not be obtained.

## Thanks
- Team of Backtrader: Very simple and cool library!
- Team of [FinamPy](https://github.com/cia76): for free excellent libraries for live trading by connection to brokers 

## License
[MIT](https://choosealicense.com/licenses/mit)

## Important
Error correction, revision and development of the library is carried out by the author and the community!

**Push your commits!**

## Terms of Use
The backtrader_finam library, which allows you to integrate Backtrader and MOEX API, is the **Program** created solely for the convenience of work.
When using the **Program**, the User is obliged to comply with the provisions of the current legislation of his country.
Using the **Program** are offered on an "AS IS" basis. No guarantees, either oral or written, are attached and are not provided.
The author and the community does not guarantee that all errors of the **Program** have been eliminated, respectively, the author and the community do not bear any responsibility for
the consequences of using the **Program**, including, but not limited to, any damage to equipment, computers, mobile devices,
User software caused by or related to the use of the **Program**, as well as for any financial losses
incurred by the User as a result of using the **Program**.
No one is responsible for data loss, losses, damages, including accidental or indirect, lost profits, loss of revenue or any other losses
related to the use of the **Program**.

The **Program** is distributed under the terms of the [MIT](https://choosealicense.com/licenses/mit ) license.
