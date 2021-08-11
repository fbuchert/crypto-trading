import base64
import hmac
import hashlib
import websockets
import json
import asyncio
import time
import logging
from typing import DefaultDict, Dict, List, Optional, Tuple, Set
from collections import defaultdict

from core.instrument import Instrument
from core.quote import Quote
from core.tick import Tick
from core.order_update import OrderUpdate
from core.fill import Fill
from core.events import TickEvent, QuoteEvent, OrderUpdateEvent, FillEvent
from clients.websocket_base import WebsocketBase

from core.const import KRAKEN_NAME_TO_INSTRUMENTS, KRAKEN_TICKER_TO_INSTRUMENTS


rootLogger = logging.getLogger()


def is_subscription_message(msg: Dict) -> bool:
    is_dict = isinstance(msg, dict)
    if is_dict and 'event' in msg.keys() and (msg['event'] == 'subscribed' or msg['event'] == 'unsubscribed'):
        return True
    return False


def is_challenge(msg: Dict) -> bool:
    is_dict = isinstance(msg, dict)
    if is_dict and 'event' in msg.keys() and msg['event'] == 'challenge':
        return True
    return False


def is_heartbeat(msg: Dict) -> bool:
    return msg.get('feed', '') == 'heartbeat'


def is_alert(msg: Dict) -> bool:
    return msg.get('event', '') == 'alert'


def is_feed_msg(msg: Dict) -> bool:
    return 'feed' in msg.keys()


def is_error(msg: Dict) -> bool:
    return msg.get('event', '') == 'error'


def get_subscription_key(channel: str, instrument: Optional[Instrument] = None, freq: Optional[str] = None) -> str:
    instrument_id = instrument.instrument_id if instrument is not None else None
    return '.'.join((param for param in [channel, instrument_id, freq] if param is not None))


class KrakenFuturesWSClient(WebsocketBase):
    _ENDPOINT = 'wss://futures.kraken.com/ws/v1'

    def __init__(self, api_keys: Optional[Dict] = None, websocket_id: str = 'kraken_futures_websocket'):
        super().__init__(websocket_id)
        self.ws = None
        self._api_keys = api_keys
        self.keepalive = False

        self._original_challenge = None
        self._signed_challenge = None
        self._is_authenticated = None

        self._feed_subscriptions: Set[str] = set()
        self._consumer_subscriptions: DefaultDict[str, List] = defaultdict(list)

    def _get_url(self) -> str:
        return self._ENDPOINT

    ########################
    # WEBSOCKET CONNECTION #
    ########################
    async def _keepalive(self) -> None:
        await self.ws.send(json.dumps({'event': 'subscribe', 'feed': 'heartbeat'}))

    async def _authenticate(self) -> None:
        await self.ws.send(json.dumps({'event': 'challenge', 'api_key': self._api_keys['key']}))

        while not self._is_authenticated:
            await asyncio.sleep(0.1)

    async def _connect(self, keepalive: bool = True) -> None:
        # If already connected, don't reconnect
        if self.ws:
            return

        try:
            self.ws = await websockets.connect(self._get_url())
            _ = await self.ws.recv()

            if keepalive:
                await self._keepalive()
                self.keepalive = keepalive

            self.is_running = True
        except Exception as e:
            rootLogger.error(f'Error in connection process of {self.websocket_id}-websocket: {e}')

    async def _reconnect(self, reconnection_interval: int = 0.5) -> None:
        await self.ws.close()
        self.ws = None
        self._is_authenticated = False

        await asyncio.sleep(reconnection_interval)
        await self._connect(self.keepalive)

        for sub_key in self._feed_subscriptions:
            await self._subscribe(*sub_key.split('.'), force=True)

    async def start(self, keepalive: bool = True) -> None:
        await self._connect(keepalive)

        # Infinite loop
        while self.is_running:
            try:
                if not self.ws.open:
                    await self._reconnect()
                    rootLogger.info(f'Reopened {self.websocket_id}-websocket connection.')
                else:
                    data = await self.ws.recv()
                    msg = json.loads(data)
                    self._on_message(msg)
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
    async def _send_command(self, params: Dict) -> None:
        await self.ws.send(json.dumps({
                **params,
                'api_key': self._api_keys['key'],
                'original_challenge': self._original_challenge,
                'signed_challenge': self._signed_challenge
            }
        ))

    async def _subscribe(self, channel: str, instrument: Optional[Instrument] = None, consumer: object = None, force: bool = False) -> None:
        sub_key = get_subscription_key(channel, instrument)
        if sub_key not in self._feed_subscriptions or force:
            cmd_params = {"event": "subscribe", "feed": channel}
            if instrument is not None:
                cmd_params['product_ids'] = [instrument.instrument_id]
            await self._send_command(cmd_params)
            self._feed_subscriptions.add(sub_key)

        if consumer is not None:
            self._subscribe_consumer(sub_key, consumer)

    def _subscribe_consumer(self, sub_key: str, consumer: object) -> None:
        subscribed_consumers = self._consumer_subscriptions[sub_key]

        if consumer not in subscribed_consumers:
            self._consumer_subscriptions[sub_key].append(consumer)
            rootLogger.info(f'Subscribed consumer {consumer} to subscription key {sub_key}')

    async def _unsubscribe(self, channel: str, instrument: Optional[Instrument] = None, consumer: object = None) -> None:
        sub_key = get_subscription_key(channel, instrument)

        if consumer is not None:
            self._unsubscribe_consumer(sub_key, consumer)

        if sub_key in self._feed_subscriptions and len(self._consumer_subscriptions[sub_key]) == 0:
            cmd_params = {'event': 'unsubscribe', 'feed': channel}
            if instrument is not None:
                cmd_params['product_ids'] = [instrument.instrument_id]
            await self._send_command(cmd_params)
            self._feed_subscriptions.remove(sub_key)

    def _unsubscribe_consumer(self, sub_key: str, consumer: object) -> None:
        try:
            self._consumer_subscriptions[sub_key].remove(consumer)
            rootLogger.info(f'Unsubscribed consumer {consumer} to subscription key {sub_key}')
        except Exception as e:
            rootLogger.error(f'Error when unsubscribing consumer {e}')

    async def subscribe_fills(self, consumer: object = None) -> None:
        if not self._is_authenticated:
            await self._authenticate()
        await self._subscribe('fills', consumer=consumer)

    async def unsubscribe_fills(self, consumer: object = None) -> None:
        await self._unsubscribe('fills', consumer=consumer)

    async def subscribe_orders(self, consumer: object = None) -> None:
        if not self._is_authenticated:
            await self._authenticate()
        await self._subscribe('open_orders', consumer=consumer)

    async def unsubscribe_orders(self, consumer: object = None) -> None:
        await self._unsubscribe('open_orders', consumer=consumer)

    async def subscribe_trades(self, instrument: Instrument, consumer: object = None) -> None:
        await self._subscribe('trade', instrument, consumer)

    async def unsubscribe_trades(self, instrument: Instrument, consumer: object = None) -> None:
        await self._unsubscribe('trade', instrument, consumer)

    async def subscribe_quotes(self, instrument: Instrument, consumer: object = None) -> None:
        await self._subscribe('ticker', instrument, consumer)

    async def unsubscribe_quotes(self, instrument: Instrument, consumer: object = None) -> None:
        await self._unsubscribe('ticker', instrument, consumer)

    async def subscribe_bars(self, instrument: Instrument, freq: str, consumer: object = None) -> None:
        raise NotImplementedError('Subscription of OHLCV-bars is not implemented yet.')

    async def unsubscribe_bars(self, instrument: Instrument, freq: str, consumer: object = None) -> None:
        raise NotImplementedError('Unsubscription of OHLCV-bars is not implemented yet.')

    ####################
    # MESSAGE HANDLERS #
    ####################
    def _on_message(self, msg: Dict) -> None:
        print(msg)
        if is_error(msg):
            rootLogger.error(f'Received error message on {self.websocket_id}-websocket stream: {msg}')
        else:
            self._handle_message(msg)

    def _handle_message(self, msg: Dict) -> None:
        if is_challenge(msg):
            self._handle_challenge(msg)
        elif is_subscription_message(msg):
            self._handle_subscription_msg(msg)
        elif is_heartbeat(msg):
            self._handle_heartbeat(msg)
        elif is_alert(msg):
            self._handle_alert_msg(msg)
        elif is_feed_msg(msg):
            event_list = self._handle_feed_message(msg)

            for sub_key, event in event_list:
                for consumer in self._consumer_subscriptions[sub_key]:
                    consumer.handle_event(event)
        else:
            rootLogger.info(f'Received message on {self.websocket_id}-websocket stream on unknown channel: {msg}')

    def _handle_challenge(self, msg: Dict) -> None:
        self._original_challenge = msg["message"]
        self._signed_challenge = self._sign_challenge(msg)
        self._is_authenticated = True

    def _handle_subscription_msg(self, msg: Dict) -> None:
        rootLogger.info(f'Received subscription message at {self.websocket_id}-websocket: {msg}')

    def _handle_heartbeat(self, msg: Dict) -> None:
        # One could add an implementation of a timeout to detect connectivity issues.
        pass

    def _handle_alert_msg(self, msg: Dict) -> None:
        rootLogger.info(f'Received alert message at {self.websocket_id}: {msg}')

    def _handle_feed_message(self, msg:  Dict) -> List:
        event_list = []
        if msg["feed"] == "ticker":
            event_list = self._handle_ticker_msg(msg)
        elif msg["feed"] == "fills_snapshot" or msg["feed"] == "fills":
            event_list = self._handle_fills_msg(msg)
        elif msg["feed"] == "open_orders_snapshot" or msg["feed"] == "open_orders":
            event_list = self._handle_open_order_msg(msg)
        elif msg["feed"] == "trade_snapshot" or msg["feed"] == "trade":
            event_list = self._handle_trade_msg(msg)
        else:
            rootLogger.error(f'Received message of unknown {self.websocket_id}-websocket channel: {msg}.')
        return event_list

    def _handle_open_order_msg(self, msg: Dict) -> List[Tuple[str, OrderUpdateEvent]]:
        event_list = []
        sub_key = get_subscription_key('open_orders')

        order_messages = msg['orders'] if 'orders' in msg.keys() else [msg['order']]
        for order_msg in order_messages:
            instrument = KRAKEN_TICKER_TO_INSTRUMENTS[order_msg['instrument']]
            order_update = OrderUpdate.from_kraken_fut_msg(instrument, order_msg)
            event_list.append((sub_key, OrderUpdateEvent(order_update, publisher_id=self.websocket_id)))
        return event_list

    def _handle_ticker_msg(self, msg: Dict) -> List[Tuple[str, QuoteEvent]]:
        instrument = KRAKEN_TICKER_TO_INSTRUMENTS[msg['product_id']]
        sub_key = get_subscription_key('ticker', instrument)
        return [(sub_key, QuoteEvent(Quote.from_kraken_fut_msg(instrument, msg), publisher_id=self.websocket_id))]

    def _handle_trade_msg(self, msg: Dict) -> List[Tuple[str, TickEvent]]:
        instrument = KRAKEN_TICKER_TO_INSTRUMENTS[msg['product_id']]
        sub_key = get_subscription_key('trade', instrument)

        tick_events = []
        tick_msgs = msg['trades'] if 'trades' in msg.keys() else [msg]
        for tick_msg in tick_msgs:
            tick = Tick.from_kraken_fut_msg(instrument, tick_msg)
            tick_events.append((sub_key, TickEvent(tick, publisher_id=self.websocket_id)))
        return tick_events

    def _handle_fills_msg(self, msg: Dict) -> List[Tuple[str, FillEvent]]:
        event_list = []
        sub_key = get_subscription_key('fills')

        for fill_msg in msg['fills']:
            instrument = KRAKEN_TICKER_TO_INSTRUMENTS[fill_msg['instrument']]
            fill = Fill.from_kraken_fut_msg(instrument, fill_msg)
            event_list.append((sub_key, FillEvent(fill, publisher_id=self.websocket_id)))
        return event_list

    def _sign_challenge(self, msg: Dict) -> Optional[str]:
        """
        Based on https://github.com/CryptoFacilities/WebSocket-v1-Python/blob/master/cfWebSocketApiV1.py.
        """
        try:
            sha256_hash = hashlib.sha256()
            sha256_hash.update(msg["message"].encode("utf8"))
            hash_digest = sha256_hash.digest()
            secret_decoded = base64.b64decode(self._api_keys["secret"])
            hmac_digest = hmac.new(secret_decoded, hash_digest, hashlib.sha512).digest()
            sch = base64.b64encode(hmac_digest).decode("utf-8")
            return sch
        except Exception as e:
            rootLogger.error(f"Error signing challenge upon websocket authentication: {e}")
            return None
