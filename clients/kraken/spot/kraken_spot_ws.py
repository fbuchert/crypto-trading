import json
import asyncio
import logging
import websockets

from collections import defaultdict
from typing import Optional, Dict, List, DefaultDict, Union, Set, Tuple

from core.instrument import Instrument
from core.quote import Quote
from core.tick import Tick
from core.events import TickEvent, QuoteEvent
from clients.websocket_base import WebsocketBase
from core.const import KRAKEN_TICKER_TO_INSTRUMENTS

rootLogger = logging.getLogger()


def is_subscription_msg(msg: Union[List, Dict]) -> bool:
    return isinstance(msg, Dict) and msg['event'] == 'subscriptionStatus'


def is_feed_msg(msg: Union[List, Dict]) -> bool:
    return isinstance(msg, List)


def is_pong_msg(msg: Union[List, Dict]) -> bool:
    return isinstance(msg, Dict) and msg['event'] == 'pong'


def is_heartbeat_msg(msg: Union[List, Dict]) -> bool:
    return isinstance(msg, Dict) and msg['event'] == 'heartbeat'


def is_error(msg: Union[List, Dict]):
    return isinstance(msg, Dict) and msg['event'] == 'error'


def get_subscription_key(channel: str, instrument: Optional[Instrument] = None, freq: Optional[str] = None) -> str:
    instrument_id = instrument.instrument_id if instrument is not None else None
    return '.'.join((param for param in [channel, instrument_id, freq] if param is not None))


class KrakenSpotWSClient(WebsocketBase):
    _ENDPOINT = 'wss://ws.kraken.com'

    def __init__(self, api_keys: Optional[Dict] = None, websocket_id: str = 'kraken_spot_websocket'):
        super().__init__(websocket_id)
        self._api_keys = api_keys
        self.ws = None
        self.keepalive = False
        self._is_authenticated = None

        self._feed_subscriptions: Set[str] = set()
        self._consumer_subscriptions: DefaultDict[str, List] = defaultdict(list)

    def _get_url(self) -> str:
        return self._ENDPOINT

    ########################
    # WEBSOCKET CONNECTION #
    ########################
    async def _keepalive(self, interval: int = 30) -> None:
        while True:
            try:
                if self.ws.open:
                    await self.ws.send(json.dumps({"event": "ping"}))
            except Exception as e:
                rootLogger.error(f'Error running keepalive for {self.websocket_id}-websocket connection: {e}')
            await asyncio.sleep(interval)

    async def _authenticate(self):
        # TODO: Implement authentication method via REST API
        pass

    async def _connect(self, keepalive: bool = True) -> None:
        if self.ws is not None:
            return

        try:
            self.ws = await websockets.connect(self._get_url())

            if keepalive:
                _ = asyncio.create_task(self._keepalive())
                self.keepalive = keepalive

            self.is_running = True
        except Exception as e:
            rootLogger.error(f'Error in connection process of {self.websocket_id}-websocket: {e}')

    async def _reconnect(self, reconnection_interval: int = 10) -> None:
        await self.ws.close()
        self.ws = None
        self._is_authenticated = False

        await asyncio.sleep(reconnection_interval)
        await self._connect(self.keepalive)

        for sub_key in self._feed_subscriptions:
            await self._subscribe(*sub_key.split('_'), force=True)

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
                    self._on_message(msg)
            except Exception as e:
                rootLogger.error(f'Error in running {self.websocket_id}-websocket: {e}')

    async def close(self):
        self.is_running = False
        await self.ws.close()
        self.ws = None
        rootLogger.info(f'Closed {self.websocket_id}-websocket connection.')

    ###########################
    # SUBSCRIBE / UNSUBSCRIBE #
    ###########################
    async def _send_command(self, params: Dict):
        await self.ws.send(json.dumps(params))

    async def _subscribe(self, channel: str, instrument: Optional[Instrument] = None, consumer: object = None, force: bool = False):
        sub_key = get_subscription_key(channel, instrument)

        if sub_key not in self._feed_subscriptions or force:
            cmd_params = {"event": "subscribe", "subscription": {'name': channel}}
            if instrument is not None:
                cmd_params["pair"] = [instrument.instrument_id]
            if self._is_authenticated:
                cmd_params['subscription']['token'] = self._signed_challenge
            await self._send_command(cmd_params)
            self._feed_subscriptions.add(sub_key)

        if consumer is not None:
            self._subscribe_consumer(sub_key, consumer)

    def _subscribe_consumer(self, sub_key: str, consumer: object) -> None:
        subscribed_consumers = self._consumer_subscriptions[sub_key]

        if consumer not in subscribed_consumers:
            self._consumer_subscriptions[sub_key].append(consumer)
            rootLogger.info(f'Subscribed consumer {consumer} to subscription key {sub_key}')

    async def _unsubscribe(self, channel: str, instrument: Optional[Instrument] = None, consumer: object = None, force: bool = False):
        sub_key = get_subscription_key(channel, instrument)

        if consumer is not None:
            self._unsubscribe_consumer(sub_key, consumer)

        if sub_key in self._feed_subscriptions and len(self._consumer_subscriptions[sub_key]) == 0:
            cmd_params = {"event": "unsubscribe", "subscription": {'name': channel}}
            if instrument is not None:
                cmd_params["pair"] = [instrument.instrument_id]
            if self._is_authenticated:
                cmd_params['subscription']['token'] = self._signed_challenge
            await self._send_command(cmd_params)
            self._feed_subscriptions.remove(sub_key)

    def _unsubscribe_consumer(self, sub_key: str, consumer: object) -> None:
        try:
            self._consumer_subscriptions[sub_key].remove(consumer)
            rootLogger.info(f'Unsubscribed consumer {consumer} to subscription key {sub_key}')
        except Exception as e:
            rootLogger.error(f'Error when unsubscribing consumer {e}')

    async def subscribe_orders(self, consumer: object = None) -> None:
        # TODO: Authentication method is not implemented yet
        if not self._is_authenticated:
            await self._authenticate()
        await self._subscribe('openOrders', consumer=consumer)

    async def unsubscribe_orders(self, consumer: object = None) -> None:
        await self._unsubscribe('openOrders', consumer=consumer)

    async def subscribe_trades(self, instrument: Instrument, consumer: object = None) -> None:
        await self._subscribe('trade', instrument, consumer)

    async def unsubscribe_trades(self, instrument: Instrument, consumer: object = None) -> None:
        await self._unsubscribe('trade', instrument, consumer)

    async def subscribe_quotes(self, instrument: Instrument, consumer: object = None) -> None:
        await self._subscribe('spread', instrument, consumer)

    async def unsubscribe_quotes(self, instrument: Instrument, consumer: object = None) -> None:
        await self._unsubscribe('spread', instrument, consumer)

    async def subscribe_bars(self, instrument: Instrument, freq: str, consumer: object = None) -> None:
        raise NotImplementedError('Subscription of OHLCV-bars is not implemented yet.')

    async def unsubscribe_bars(self, instrument: Instrument, freq: str, consumer: object = None) -> None:
        raise NotImplementedError('Unsubscription of OHLCV-bars is not implemented yet.')

    ####################
    # MESSAGE HANDLERS #
    ####################
    def _on_message(self, msg: Union[List, Dict]) -> None:
        if is_error(msg):
            rootLogger.error(f'Received error message on {self.websocket_id}-websocket stream: {msg}')
        else:
            self._handle_message(msg)

    def _handle_message(self, msg: Union[List, Dict]):
        if is_subscription_msg(msg):
            self._handle_subscription_msg(msg)
        elif is_pong_msg(msg) or is_heartbeat_msg(msg):
            self._handle_pong_msg(msg)
        elif is_feed_msg(msg):
            event_list = self._handle_feed_message(msg)

            for key, event in event_list:
                for consumer in self._consumer_subscriptions[key]:
                    consumer.handle_event(event)
        else:
            rootLogger.info(f'Received message on {self.websocket_id}-websocket stream on unknown channel: {msg}')

    def _handle_subscription_msg(self, msg: List) -> None:
        rootLogger.info(f'Received subscription message at {self.websocket_id}-websocket: {msg}')

    def _handle_pong_msg(self, msg: List):
        # One could add an implementation of a timeout to detect connectivity issues.
        pass

    def _handle_feed_message(self, msg: List) -> List:
        event_list = []
        if msg[-2] == 'trade':
            event_list = self._handle_trade_msg(msg)
        elif msg[-2] == 'spread':
            event_list = self._handle_ticker_msg(msg)
        elif msg[-2] == 'openOrders':
            event_list = self._handle_orders_msg(msg)
        else:
            rootLogger.error(f'Received message of unknown {self.websocket_id}-websocket channel: {msg}.')
        return event_list

    def _handle_orders_msg(self, msg: List):
        # TODO: Implement handle ownOrder messages after authentication mechanism has been established
        return []

    def _handle_trade_msg(self, msg: List) -> List[Tuple[str, TickEvent]]:
        instrument = KRAKEN_TICKER_TO_INSTRUMENTS[msg[-1]]
        sub_key = get_subscription_key('trade', instrument)

        event_list = []
        for trade_msg in msg[1]:
            event_list.append((sub_key, TickEvent(Tick.from_kraken_spot_msg(instrument, trade_msg), publisher_id=self.websocket_id)))
        return event_list

    def _handle_ticker_msg(self, msg: List) -> List[Tuple[str, QuoteEvent]]:
        instrument = KRAKEN_TICKER_TO_INSTRUMENTS[msg[-1]]
        sub_key = get_subscription_key('spread', instrument)
        return [(sub_key, QuoteEvent(Quote.from_kraken_spot_msg(instrument, msg), publisher_id=self.websocket_id))]
