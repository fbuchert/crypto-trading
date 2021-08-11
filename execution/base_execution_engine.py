import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Callable

from core.trade import Trade
from core.instrument import Instrument
from clients.api_client_base import APIClientBase
from clients.websocket_base import WebsocketBase


rootLogger = logging.getLogger()


class BaseExecutionEngine(ABC):
    def __init__(self, name: str = 'execution_engine', save_path: Optional[str] = None):
        super().__init__()
        self.name = name
        self.active_trades: Dict[int, Trade] = {}
        self.ws_client: Optional[WebsocketBase] = None
        self.api_client: Optional[APIClientBase] = None

        self.save_path = save_path
        self.save_order_event_dicts = True if self.save_path is not None else False

        if self.save_path and not os.path.exists(self.save_path):
            os.makedirs(self.save_path, exist_ok=True)

    def set_ws_client(self, ws_client: WebsocketBase):
        self.ws_client = ws_client

    def set_api_client(self, api_client: APIClientBase):
        self.api_client = api_client

    async def start(self):
        if self.api_client is None or self.ws_client is None:
            raise ValueError(f'API client {self.api_client} or {self.ws_client} of {self.name} is not set.')
        await self.ws_client.subscribe_orders(consumer=self)
        await self.ws_client.subscribe_fills(consumer=self)

    async def close(self):
        await self.ws_client.unsubscribe_orders(consumer=self)
        await self.ws_client.unsubscribe_fills(consumer=self)

    @abstractmethod
    def handle_event(self, **kwargs):
        pass

    @abstractmethod
    def execute_trade(self, instrument: Instrument, size: float, exec_callback: Callable):
        pass
