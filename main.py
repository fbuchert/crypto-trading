import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict

import yaml

from clients.ftx.ftx_api_wrapper import FTXClientWrapper
from clients.ftx.ftx_websocket import FTXWebsocketClient
from core.const import FTX_NAME_TO_INSTRUMENTS
from execution.ftx.ftx_execution_engine import FTXExecutionEngine
from portfolio.portfolio import Portfolio
from strategy.strategy_implementations.example_strategy import ExampleBarStrategy

MODULE_MAP = {
    "ExampleStrategy": ExampleBarStrategy,
    "Portfolio": Portfolio
}


def initialize_root_logger(file_path: str = '') -> logging.Logger:
    log_formatter = logging.Formatter("%(asctime)s [%(threadName)s] [%(filename)s:%(lineno)d] [%(levelname)s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)

    if file_path:
        path = os.path.split(file_path)[0]
        if not os.path.exists(path):
            os.makedirs(path)
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(log_formatter)
        rootLogger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    rootLogger.addHandler(console_handler)
    return rootLogger


async def start_strategy(config: Dict):
    strategy = ExampleBarStrategy(config)
    loop = asyncio.get_event_loop()
    loop.create_task(strategy.start())


if __name__ == '__main__':
    log_path = "./logs/ftx/"
    file_name = datetime.now(timezone(timedelta(0))).strftime("%Y-%m-%d %H:%M:%S")
    rootLogger = initialize_root_logger(os.path.join(log_path, file_name))

    with open('config.yaml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    if config['exchange']['name'] == 'ftx':
        config['exchange']['api_client'] = FTXClientWrapper
        config['exchange']['websocket_client'] = FTXWebsocketClient
        config['execution_engine'] = FTXExecutionEngine

        config['strategy'] = MODULE_MAP[config['strategy']]
        config['portfolio_manager'] = MODULE_MAP[config['portfolio_manager']]

        config['instruments'] = list(map(lambda x: FTX_NAME_TO_INSTRUMENTS[x], config['instruments']))
    elif config['exchange']['name'] == 'kraken_spot':
        raise NotImplementedError('Platform does not fully support trading on Kraken spot exchange yet.')
    elif config['exchange']['name'] == 'kraken_futures':
        raise NotImplementedError('Platform does not fully support trading on Kraken spot exchange yet.')

    loop = asyncio.get_event_loop()
    loop.create_task(start_strategy(config))
    loop.run_forever()
