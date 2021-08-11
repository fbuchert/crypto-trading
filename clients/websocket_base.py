from typing import Dict
from abc import ABC, abstractmethod


class WebsocketBase(ABC):
    def __init__(self, websocket_id: str, **kwargs):
        self.websocket_id = websocket_id
        self.is_running = False

    @abstractmethod
    async def start(self, keepalive: bool = True):
        pass

    @abstractmethod
    async def close(self, **kwargs):
        pass

    @abstractmethod
    def _keepalive(self, **kwargs):
        pass

    @abstractmethod
    def _connect(self,**kwargs):
        pass

    @abstractmethod
    def _subscribe(self, **kwargs):
        pass

    @abstractmethod
    def _unsubscribe(self, **kwargs):
        pass

    @abstractmethod
    def _on_message(self, msg: Dict):
        pass

    @abstractmethod
    def _handle_message(self, msg: Dict):
        pass

    @abstractmethod
    def subscribe_orders(self, **kwargs):
        pass

    @abstractmethod
    def unsubscribe_orders(self, **kwargs):
        pass

    @abstractmethod
    def subscribe_bars(self, **kwargs):
        pass

    @abstractmethod
    def unsubscribe_bars(self, **kwargs):
        pass
