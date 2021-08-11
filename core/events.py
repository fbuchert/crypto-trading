from typing import Union
from core.event_type import EventType
from core.bar import Bar
from core.trade import Trade
from core.quote import Quote
from core.fill import Fill
from core.tick import Tick
from core.order_update import OrderUpdate


class Event(object):
    def __init__(self, _type: EventType, _data: Union[Trade, Bar, Quote, Tick, Fill, OrderUpdate], publisher_id: str):
        self._type = _type
        self._data = _data
        self._publisher_id = publisher_id

    @property
    def type(self) -> EventType:
        return self._type

    @property
    def data(self) -> Union[Trade, Bar, Quote, Tick, Fill, OrderUpdate]:
        return self._data

    @property
    def publisher_id(self) -> str:
        return self._publisher_id


# Data stream events
class BarEvent(Event):
    def __init__(self, bar: Bar, publisher_id: str = ''):
        super().__init__(EventType.BAR, bar, publisher_id)


class QuoteEvent(Event):
    def __init__(self, quote: Quote, publisher_id: str = ''):
        super().__init__(EventType.QUOTE, quote, publisher_id)


class TickEvent(Event):
    def __init__(self, tick: Tick, publisher_id: str = ''):
        super().__init__(EventType.TICK, tick, publisher_id)


class FillEvent(Event):
    def __init__(self, fill: Fill, publisher_id: str = ''):
        super().__init__(EventType.FILL, fill, publisher_id)


class OrderUpdateEvent(Event):
    def __init__(self, order_update: OrderUpdate, publisher_id: str = ''):
        super().__init__(EventType.ORDER_UPDATED, order_update, publisher_id)


# Execution Events
class TradeExecutedEvent(Event):
    def __init__(self, trade: Trade, publisher_id: str = ''):
        super().__init__(EventType.TRADE_EXECUTED, trade, publisher_id)
