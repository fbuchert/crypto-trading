import asyncio
from collections import deque
from typing import Dict, Callable

from core.instrument import Instrument
from core.order_side import OrderSide
from clients.api_client_base import APIClientBase


class Trade:
    def __init__(self, instrument: Instrument, size: float, client: APIClientBase, execution_callback: Callable):
        self.client = client
        self.instrument = instrument
        self.size = size
        self.side = OrderSide.BUY if size > 0 else OrderSide.SELL
        self.execution_callback = execution_callback

        self.trade_events = deque([])
        self.lock = asyncio.Lock()

        self.order_id = None
        self.order_status = None

    def __str__(self):
        return '{} [{} {} {}]'.format(self.order_id, self.side, self.instrument.name, self.size)

    def handle_order_update(self, event):
        raise NotImplementedError('Handle order update function not implemented in base class.')