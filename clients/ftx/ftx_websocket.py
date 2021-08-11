import hmac
import json
import copy
import time
import asyncio
import logging
import websockets
from datetime import datetime
from collections import defaultdict, deque
from typing import DefaultDict, Deque, List, Dict, Optional, Tuple, Set

from core.bar import Bar
from core.tick import Tick
from core.quote import Quote
from core.fill import Fill
from core.order_update import OrderUpdate
from core.instrument import Instrument
from core.const import FTX_TICKER_TO_INSTRUMENTS
from core.events import OrderUpdateEvent, TickEvent, QuoteEvent, FillEvent, BarEvent

from clients.websocket_base import WebsocketBase


rootLogger = logging.getLogger()


def get_subscription_key(channel: str, instrument: Optional[Instrument] = None, freq: Optional[str] = None) -> str:
    instrument_id = instrument.instrument_id if instrument is not None else None
    return '.'.join((param for param in [channel, instrument_id, freq] if param is not None))


def is_subscription_msg(msg: Dict) -> bool:
    return msg['type'] in {'subscribed', 'unsubscribed'}


def is_pong(msg: Dict) -> bool:
    return msg['type'] == 'pong'


def is_error(msg: Dict):
    return msg['type'] == 'error'


def is_info_msg(msg: Dict) -> bool:
    return msg['type'] == 'info'


def is_feed_msg(msg: Dict) -> bool:
    return msg.get('channel', '') in ['trades', 'ticker', 'fills', 'orders']


class FTXWebsocketClient(WebsocketBase):
    _ENDPOINT = 'wss://ftx.com/ws/'

    def __init__(self, api_keys: Dict, websocket_id: str = 'ftx_websocket', subaccount: str = None):
        super().__init__(websocket_id)
        self.ws = None
        self._api_keys = api_keys
        self.subaccount = subaccount
        self.keepalive = False

        self._feed_subscriptions: Set[str] = set()
        self._consumer_subscriptions: DefaultDict[str, List] = defaultdict(list)
        self._bars = {}
        self._logged_in = False

    def _get_url(self) -> str:
        return self._ENDPOINT

    ########################
    # WEBSOCKET CONNECTION #
    ########################
    async def _keepalive(self, interval: int = 30) -> None:
        while True:
            try:
                if self.ws.open:
                    await self._send_command({'op': 'ping'})
            except Exception as e:
                rootLogger.error(f'Error running keepalive for {self.websocket_id}-websocket connection: {e}')
            await asyncio.sleep(interval)

    async def _login(self) -> None:
        ts = int(time.time() * 1000)
        await self._send_command({'op': 'login', 'args': {
            'key': self._api_keys['key'],
            'sign': hmac.new(
                self._api_keys['secret'].encode(), f'{ts}websocket_login'.encode(), 'sha256').hexdigest(),
            'time': ts,
            'subaccount': self.subaccount,
        }})
        self._logged_in = True

    async def _connect(self, keepalive: bool = False) -> None:
        if self.ws:
            return

        try:
            self.ws = await websockets.connect(self._get_url())

            if keepalive:
                _ = asyncio.create_task(self._keepalive())
                self.keepalive = keepalive

            self.is_running = True
        except Exception as e:
            rootLogger.error(f'Error in connection process of {self.websocket_id}-websocket: {e}')

    async def _reconnect(self, reconnection_interval: float = 0.5) -> None:
        await self.ws.close()
        self.ws = None
        await asyncio.sleep(reconnection_interval)
        await self._connect()

        for subscription_key in self._feed_subscriptions:
            if 'bar' in subscription_key:
                channel, market, freq = subscription_key.split('.')
                await self.subscribe_bars(market, freq)
            else:
                await self._subscribe(*subscription_key.split('.'), force=True)

    async def start(self, keepalive: bool = True) -> None:
        await self._connect(keepalive)

        while self.is_running:
            try:
                if not self.ws.open:
                    await self._reconnect()
                    rootLogger.info(f"Reopened {self.websocket_id}-websocket connection.")
                else:
                    data = await self.ws.recv()
                    msg = json.loads(data)
                    await self._on_message(msg)
            except Exception as e:
                rootLogger.error(f'Error in running {self.websocket_id}-websocket: {e}')

    async def close(self) -> None:
        self.is_running = False
        await self.ws.close()
        self.ws = None
        rootLogger.info(f'Closed {self.websocket_id}-websocket connection.')

    ###########################
    # SUBSCRIBE / UNSUBSCRIBE #
    ###########################
    async def _send_command(self, message: Dict) -> None:
        await self.ws.send(json.dumps(message))

    async def _subscribe(self, channel: str, instrument: Optional[Instrument] = None, consumer: object = None, force: bool = False) -> None:
        sub_key = get_subscription_key(channel, instrument)
        if sub_key not in self._feed_subscriptions or force:
            params = {'channel': channel}
            if instrument:
                params['market'] = instrument.instrument_id
            await self._send_command({'op': 'subscribe', **params})

            self._feed_subscriptions.add(sub_key)

        if consumer is not None:
            self._subscribe_consumer(sub_key, consumer)

    def _subscribe_consumer(self, subscription_key: str, consumer: object):
        subscribed_consumers = self._consumer_subscriptions.get(subscription_key, [])

        if consumer not in subscribed_consumers:
            self._consumer_subscriptions[subscription_key].append(consumer)
            rootLogger.info(f'Subscribed consumer {consumer} to subscription key {subscription_key}')

    async def _unsubscribe(self, channel: str, instrument: Optional[Instrument] = None, consumer: object = None) -> None:
        subscription_key = get_subscription_key(channel, instrument)

        if consumer is not None:
            self._unsubscribe_consumer(subscription_key, consumer)

        if subscription_key in self._feed_subscriptions and len(self._consumer_subscriptions[subscription_key]) == 0:
            params = {'channel': channel}
            if instrument:
                params['market'] = instrument.instrument_id
            await self._send_command({'op': 'unsubscribe', **params})
            self._feed_subscriptions.remove(subscription_key)

    def _unsubscribe_consumer(self, subscription_key: str, consumer: object) -> None:
        try:
            self._consumer_subscriptions[subscription_key].remove(consumer)
            rootLogger.info(f'Unsubscribed consumer {consumer} to subscription key {subscription_key}')
        except Exception as e:
            rootLogger.error(f'Error when unsubscribing consumer {e}')

    async def subscribe_fills(self, consumer: object = None) -> None:
        if not self._logged_in:
            await self._login()
        await self._subscribe('fills', consumer=consumer)

    async def unsubscribe_fills(self, consumer: object = None) -> None:
        await self._unsubscribe('fills', consumer=consumer)

    async def subscribe_orders(self, consumer: object = None) -> None:
        if not self._logged_in:
            await self._login()
        await self._subscribe('orders', consumer=consumer)

    async def unsubscribe_orders(self, consumer: object = None) -> None:
        await self._unsubscribe('orders', consumer=consumer)

    async def subscribe_trades(self, instrument: Instrument, consumer: object = None) -> None:
        await self._subscribe('trades', instrument, consumer=consumer)

    async def unsubscribe_trades(self, instrument: Instrument, consumer: object = None) -> None:
        await self._unsubscribe('trades', instrument, consumer=consumer)

    async def subscribe_quotes(self, instrument: Instrument, consumer: object = None) -> None:
        await self._subscribe('ticker', instrument, consumer)

    async def unsubscribe_quotes(self, instrument: Instrument, consumer: object = None) -> None:
        await self._unsubscribe('ticker', instrument, consumer)

    async def subscribe_bars(self, instrument: Instrument, freq: str, consumer: object = None) -> None:
        # FTX does not provide bar data
        await self.subscribe_trades(instrument)
        self._initialize_bar_variables(instrument, freq)

        sub_key = get_subscription_key('bar', instrument, freq)
        if consumer is not None:
            self._subscribe_consumer(sub_key, consumer)

    def _initialize_bar_variables(self, instrument: Instrument, freq: str) -> None:
        if instrument.instrument_id not in self._bars.keys():
            self._bars[instrument.instrument_id] = {}
        if freq not in self._bars[instrument.instrument_id].keys():
            self._bars[instrument.instrument_id][freq] = Bar(instrument, freq)

    async def unsubscribe_bars(self, instrument: Instrument,  freq: str, consumer: object = None):
        sub_key = get_subscription_key('bar', instrument, freq)

        if consumer is not None:
            self._unsubscribe_consumer(sub_key, consumer)

        trade_key = get_subscription_key('trades', instrument)
        has_consumers = len(self._consumer_subscriptions[sub_key]) > 0 and len(self._consumer_subscriptions[trade_key]) > 0
        if trade_key in self._feed_subscriptions and not has_consumers:
            await self.unsubscribe_trades(instrument)

    ####################
    # MESSAGE HANDLERS #
    ####################
    async def _on_message(self, msg: Dict) -> None:
        if is_error(msg):
            rootLogger.info(f'Received error message on {self.websocket_id}-websocket stream: {msg}')
        else:
            await self._handle_message(msg)

    async def _handle_message(self, msg: Dict) -> None:
        if is_subscription_msg(msg):
            self._handle_subscription_msg(msg)
        elif is_info_msg(msg):
            await self._handle_info_msg(msg)
        elif is_pong(msg):
            self._handle_pong_msg(msg)
        elif is_feed_msg(msg):
            event_list = self._handle_feed_message(msg)

            for sub_key, event in event_list:
                for consumer in self._consumer_subscriptions[sub_key]:
                    consumer.handle_event(event)
        else:
            rootLogger.info(f'Received message on {self.websocket_id}-websocket stream on unknown channel: {msg}')

    def _handle_subscription_msg(self, msg: Dict) -> None:
        rootLogger.info(f'Subscription message received at {self.websocket_id}: {msg}.')

    async def _handle_info_msg(self, msg: Dict) -> None:
        rootLogger.info('Info message received: {}'.format(msg))
        if msg['code'] == 20001:
            rootLogger.info('Resubscribing data streams upon server restart.')
            await self._reconnect()

    def _handle_pong_msg(self, msg: Dict) -> None:
        # One could add an implementation of a timeout to detect connectivity issues.
        pass

    def _handle_feed_message(self, msg: Dict) -> List:
        event_list = []
        if msg['channel'] == 'trades':
            event_list.extend(self._parse_trades_message(msg))
            event_list.extend(self._parse_bars_message(msg))
        elif msg['channel'] == 'ticker':
            event_list.extend(self._parse_ticker_message(msg))
        elif msg['channel'] == 'fills':
            event_list.extend(self._parse_fills_message(msg))
        elif msg['channel'] == 'orders':
            event_list.extend(self._parse_orders_message(msg))
        else:
            rootLogger.info(f'Received message on {self.websocket_id}-websocket stream on unknown channel: {msg}')
        return event_list

    def _parse_trades_message(self, msg: Dict) -> List[Tuple[str, TickEvent]]:
        instrument = FTX_TICKER_TO_INSTRUMENTS[msg['market']]
        sub_key = get_subscription_key('trades', instrument)
        return [
            (
                sub_key,
                TickEvent(tick=Tick.from_ftx_msg(instrument, trade_msg), publisher_id=self.websocket_id)
            )
            for trade_msg in msg['data']
        ]

    def _parse_ticker_message(self, msg: Dict) -> List[Tuple[str, QuoteEvent]]:
        instrument = FTX_TICKER_TO_INSTRUMENTS[msg['market']]
        sub_key = get_subscription_key('ticker', instrument)
        return [(sub_key, QuoteEvent(Quote.from_ftx_msg(instrument, msg), self.websocket_id))]

    def _parse_orders_message(self, msg: Dict) -> List[Tuple[str, OrderUpdateEvent]]:
        instrument = FTX_TICKER_TO_INSTRUMENTS[msg['data']['market']]
        sub_key = get_subscription_key('orders')
        return [(sub_key, OrderUpdateEvent(OrderUpdate.from_ftx_msg(instrument, msg['data']), self.websocket_id))]

    def _parse_fills_message(self, msg: Dict) -> List[Tuple[str, FillEvent]]:
        instrument = FTX_TICKER_TO_INSTRUMENTS[msg['data']['market']]
        sub_key = get_subscription_key('fills')
        return [(sub_key, FillEvent(Fill.from_ftx_msg(instrument, msg), self.websocket_id))]

    def _parse_bars_message(self, msg: Dict) -> List[Tuple[str, BarEvent]]:
        bar_events = []
        if msg['market'] in self._bars.keys():
            bar_events.extend(self._update_bars(msg))
        return bar_events

    def _update_bars(self, msg: Dict) -> List[Tuple[str, BarEvent]]:
        bar_updates = []
        curr_market_bars = self._bars[msg['market']]
        for freq, bar in curr_market_bars.items():
            bar_updates.extend(self._update_bar(msg, bar))
        return bar_updates

    def _update_bar(self, msg: Dict, current_bar: Bar) -> List[Tuple[str, BarEvent]]:
        bar_events = []
        sub_key = get_subscription_key('bar', current_bar.instrument, current_bar.freq)
        for idx, trade_data in enumerate(msg['data']):
            trade_ts = datetime.fromisoformat(trade_data['time']).timestamp()
            if current_bar.is_complete(trade_ts):
                # Current bar is completed and should be published; initialize new bar object
                bar_events.append((sub_key, BarEvent(copy.copy(current_bar), self.websocket_id)))
                current_bar.reset()
            current_bar.update_bar(trade_ts, trade_data['price'], trade_data['size'])

        # Generate bar update events every time bar is updated (not only if it's completed).
        bar_events.append((sub_key, BarEvent(copy.copy(current_bar), self.websocket_id)))
        return bar_events
