import asyncio
import logging

from typing import Dict, Callable

from core.instrument import Instrument
from core.events import OrderUpdateEvent
from clients.api_client_base import APIClientBase

from core.trade import Trade
from core.order_status import OrderStatus
from core.order_type import OrderType
from core.order_side import OrderSide
from core.order_update import OrderUpdate
from execution.utils import get_rounded_size

rootLogger = logging.getLogger()


class MarketTrade(Trade):
    def __init__(self, instrument: Instrument, size: float, client: APIClientBase, execution_callback: Callable):
        size = get_rounded_size(size, instrument)
        super().__init__(instrument, size, client, execution_callback)
        self.order_status = None
        self.order_type = OrderType.MKT

    async def start(self, lock_acquired: bool = False, **kwargs) -> str:
        bid_dict, ask_dict = self._get_quotes()

        if not lock_acquired:
            await self.lock.acquire()
            lock_acquired = True

        client_resp = self._place_order()

        if client_resp.get('status', None) == 'new':
            self._handle_order_placed(client_resp, bid_dict, ask_dict)
        else:
            rootLogger.error(f'Error when placing market order: {client_resp}')
            await asyncio.sleep(0.5)
            return await self.start(lock_acquired)
        self.lock.release()
        return self.order_id

    async def handle_order_update(self, event: OrderUpdateEvent):
        await self.lock.acquire()
        self.order_status = event.data.status
        self.trade_events.append(event.data)

        if self.order_status == OrderStatus.CLOSED:
            if event.data.remaining_size > 0:
                raise ValueError(f'Remaining quantity of market order {self.order_id} is not 0 although order is closed: {order_event_dict}')
        else:
            raise ValueError(f'Unexpected event for order {self.order_id}: {event}')
        self.lock.release()

    def _get_quotes(self) -> (Dict, Dict):
        (bid,), (ask,) = self.client.get_instrument_quotes(self.instrument.instrument_id, depth=1)
        return bid, ask

    def _place_order(self) -> Dict:
        rootLogger.info(f'Placing order: {self}')
        if self.side is OrderSide.BUY:
            return self.client.buy_market(self.instrument.instrument_id, abs(self.size))
        else:
            return self.client.sell_market(self.instrument.instrument_id, abs(self.size))

    def _handle_order_placed(self, client_resp: Dict, bid_dict: Dict, ask_dict: Dict):
        order_update = OrderUpdate.from_ftx_msg(self.instrument, client_resp, bid_dict, ask_dict)
        self.order_id = order_update.order_id
        self.order_status = order_update.status
        self.trade_events.append(order_update)

    def _handle_quote_update(self, key: str, ticker_update_msg: Dict):
        raise NotImplementedError('Market orders do not support quote updates.')
