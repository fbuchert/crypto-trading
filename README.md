# Cryptocurrency Trading Application
![License](https://img.shields.io/github/license/fbuchert/crypto-trading?label=license)

This repository contains the implementation of an event-based cryptocurrency trading platform, which is run
as monolithic application. The platform has been used to trade algorithmic, quantitative trading strategies 
on cryptocurrencies for the last two years. 

## Setup & Run

```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

The `ExampleStrategy` class defined in `./strategy/strategy_implementations/example_strategy.py` implements a naive
strategy, which trades based on OHLCV-bars of arbitrary frequency. It takes buys n instrument (or keeps holding it),
for 'green' candles, i.e. close > open and sells n price. It sells

The trading strategy can be started by running:
```
python main.py
```

The strategy configuration is read from `config.yaml` with the following structure:
```
exchange:
    name: 'ftx'
    subaccount: < name of ftx subaccount >
    api_keys:
        key: < ftx_api_key >
        secret: < ftx_api_secret >

portfolio_manager: 'Portfolio' (name of portfolio module to be used)
strategy: 'ExampleStrategy' (name of portfolio module to be used)

instruments:
    - 'btc_usd_perp' (platform internal instrument names as set in './core/const.py'
    - 'eth_usd_perp'
    - ...

strategy_params:
    bar_freq: < bar frequency > (e.g. '60m' for hour bars)
    price_df_window: < length of price history strategy maintains in minutes >

trading_volume: < USD volume allocated to stratetgy, e.g 10 > 

position_save_path: < path to save current position to >
execution_save_path: < path to save execution engine dictionaries to >
```

## Testing
Unit tests of the most important system components are implemented in `./test` and can be run by
```
python -m unittest discover -v
```

<hr style="border:1px solid"> </hr>

## Repository Structure
The repository implements four main modules, which form the basis of the trading platform:
- Strategy module (`./strategy`)
- Exchange clients (`./clients`)
- Execution engine (`./execution`)
- Portfolio module (`./portfolio`)
These four components handle different tasks of the trading application as explained in the following.

---
### Exchange Clients
Implementations of exchange clients are located in the folder `./clients`.
Both REST API and websocket exchange clients are implemented for the following exchanges:

- [Kraken Futures Exchange](https://futures.kraken.com/)
- [Kraken Futures Exchange](https://futures.kraken.com/)
- [FTX](https://ftx.com/)

All exchange clients implement the abstract base classes `./clients/api_client_base.py` (REST API) and 
`./clients/websocket_base.py` (websocket clients) in order to ensure every exchange client implementation 
exhibits an uniform interface.

---
### Execution
Implementations of execution engines are located in the folder `./exeuction`.

Execution of position deltas, i.e. changes in positions of certain instrument, are handled by a separate execution engine, which - due to differences in order management
/ execution of different exchanges - has to be implemented separately for every supported exchange. All exchange-specific execution engines should implement the abstract class `BaseExecutionEngine` defined in
`./execution/base_execution_engine.py`. For now, only an implementation of an FTX execution engine supporting market orders is available. The order


Given the `instrument` and the `size` to trade as well as a callback function `exec_callback`, the engine places the
order via the exchange REST API and monitors its status using the websocket client. Upon execution, the specified
callback function is called with a `TradeExecutedEvent` as input.

#### Saving information on order execution
The executioner saves information on every order it executes in a `.csv`-file at the `execution_save_path`, which
is set in the `config.yaml`-file. The following table shows the structure of a `.csv`-file saved upon execution of a
market order.

| | timestamp | order_id | instrument | order_type | side | status | size | filled_size | remaining_size | avg_fill_price | created_at | price | client_id | bid_price | bid_size | ask_price | ask_size |
| ---------- | ------------- | ------ | ---------- | ------------- | ------ | ---------- | ------------- | ------ | ---------- | ------------- | ------ | ---------- | ------------- | ------ | ---------- | ------------- | ------ |
| 0 | 1628603102 | 69921756124 | eth_usd_perp | MKT | BUY | CREATED | 0.002 | 0.0 | 0.002 | | 1628610302 | | | 3131.5 | 32.149 | 3131.6 | 17.809 |
| 1 | 1628603102 | 69921756124 | eth_usd_perp | MKT | BUY | CLOSED | 0.002 | 0.002 | 0.0 |3131.6| 1628610302 | | | | | | |

---
### Portfolio
The portfolio module (implementation located in `./portfolio`) is used to keep track of all positions of the trading algorithm. It handles executed trades and
updates all positions accordingly. Additionally, it persists the positions to a pickle file at every update at `position_save_path`
(set in `config.yaml`), which allows for loading the current positioning upon a possible restart of the trading algorithm.

---
### Strategy
Implementations of different strategies are located in `./strategy`.

The strategy module is the central element of the trading application. It has references to instances of all previously 
described modules, i.e. exchange clients, portfolio module and execution engine and is the starting point of the application.
The `BarStrategyBase`-class (`./strategy/bar_strategy_base.py`) is an abstract 
base class, which implements the basic functionality of trading strategies developed on bars (OHLCV, tick bars, volume bars, etc.). It initializes exchange clients, a 
portfolio module and the execution engine. Upon the start of the strategy, it subscribes to the price bar streams 
for all traded assets. 

Specific strategy implementations, such as `ExampleStrategy` (`./strategy/example_strategy.py`), implement the
abstract base class as well as the `_calculate_target_position(self, price_dfs)`-function, which contains the strategy trading logic.
Given the price bars for all traded assets, the function calculates and returns the target position for each traded instrument.
Based on the difference between the current position and the target position, the strategy submits trades to the execution engine.

## TODOs
- Implement historical data management (using HDF5)
- Implement Kraken futures and spot execution engines
- Extend execution engine by supporting dynamic limit orders for optimal execution
