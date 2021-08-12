# Cryptocurrency Trading Framework
![License](https://img.shields.io/github/license/fbuchert/crypto-trading)

This repository contains the implementation of an event-based cryptocurrency trading framework, which can be used to run
trading strategies as monolithic applications. 

The framework is designed to be modular as well as extensible and allows rapid deployment trading strategies 
over multiple instruments. The implementation has been used to trade algorithmic, quantitative trading strategies 
in cryptocurrency markets.

## Overview / Structure
The repository implements four main modules, which form the basis of the trading framework:
- Exchange clients (`./clients`)
- Execution engine (`./execution`)
- Portfolio module (`./portfolio`)
- Strategy module (`./strategy`)

These four components handle different tasks of the trading application as explained in the following.

---
### Exchange Clients
Implementations of exchange clients are located in the folder `./clients`.
Both REST API and websocket exchange clients are implemented for the following exchanges:

- [Kraken Spot Exchange](https://kraken.com/)
- [Kraken Futures Exchange](https://futures.kraken.com/)
- [FTX (spot and futures)](https://ftx.com/)

All exchange clients implement the abstract base classes `./clients/api_client_base.py` (REST API) and
`./clients/websocket_base.py` (websocket clients) in order to ensure every exchange client implementation
exhibits an uniform interface.

---
### Execution Engine
Implementations of execution engines are located in the folder `./exeuction`.

The execution engine handles the execution of orders, i.e. changes of positions of the trading strategy, and 
has to be implemented separately for every supported exchange. All exchange-specific execution engines should implement 
the abstract class `BaseExecutionEngine` defined in `./execution/base_execution_engine.py`, which provides 
exchange-independent base functionalities. For now, only an implementation of an FTX execution engine supporting market 
orders is available.

#### Saving information on order execution
If required, the execution saves information on every order it executes in a `.csv`-file at `execution_save_path`, which
is set in the `config.yaml`-file (see 'Setup & Run' section). The following table shows the structure of a `.csv`-file saved upon execution of a
market order.

| | timestamp | order_id | instrument | order_type | side | status | size | filled_size | remaining_size | avg_fill_price | created_at | price | client_id | bid_price | bid_size | ask_price | ask_size |
| ---------- | ------------- | ------ | ---------- | ------------- | ------ | ---------- | ------------- | ------ | ---------- | ------------- | ------ | ---------- | ------------- | ------ | ---------- | ------------- | ------ |
| 0 | 1628603102 | 69921756124 | eth_usd_perp | MKT | BUY | CREATED | 0.002 | 0.0 | 0.002 | | 1628610302 | | | 3131.5 | 32.149 | 3131.6 | 17.809 |
| 1 | 1628603102 | 69921756124 | eth_usd_perp | MKT | BUY | CLOSED | 0.002 | 0.002 | 0.0 |3131.6| 1628610302 | | | | | | |

---
### Portfolio
The portfolio module (implementation located in `./portfolio`) is used to keep track of all positions of the trading 
strategy. It handles executed trades and updates all positions accordingly. Additionally, it persists the positions 
to a pickle file at every update at `position_save_path` (set in `config.yaml`), which allows for loading the current 
positioning upon a possible restart of the trading strategy.

---
### Strategy
Implementations of different trading strategies are located in `./strategy`.

The strategy module is the central element of the trading application. It has references to instances of all previously
described modules, i.e. exchange clients, portfolio module and execution engine and is the starting point of the 
application. As an example, an extensible implementation of trading strategies based on price bars is provided. 


The `BarStrategyBase`-class is an abstract base class, which implements the basic functionality of trading strategies developed on bars (OHLCV, tick bars, volume bars, etc.).
Specific strategy implementations, such as `ExampleStrategy`, implement the
abstract base class as well as the `_calculate_target_position(self, price_dfs)`-function, which contains the trading logic.
Given the price bars for all traded assets, the `_calculate_target_position(self, price_dfs)`-function calculates and 
returns the target position for each traded instrument. Based on the difference between the current position and the target position, the strategy submits trades to the execution engine.

The provided example strategy implements a naive long-only strategy, which trades based on OHLCV-bars of arbitrary 
frequency. The strategy takes a long position for every instrument, whose price increased over the last bar, 
i.e. close > open holds. For any instrument, whose price decreased over the last bar, i.e. close < open, it takes a
position of 0.

<hr style="border:1px solid">

## Setup & Run
The following can be used to set up a python environment in which the trading application.
```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

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

## TODOs
- Implement historical data management (using HDF5)
- Implement Kraken futures and spot execution engines
- Extend execution engine by supporting dynamic limit orders for optimal execution