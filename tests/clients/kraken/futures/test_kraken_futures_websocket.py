import unittest

import numpy as np
from core.const import KRAKEN_TICKER_TO_INSTRUMENTS
from core.order_type import OrderType
from core.order_status import OrderStatus
from core.order_side import OrderSide
from core.events import FillEvent, TickEvent, OrderUpdateEvent, QuoteEvent
from clients.kraken.futures.kraken_futures_ws import KrakenFuturesWSClient

TRADES_MSG = {
    "feed": "trade",
    "product_id": "PI_XBTUSD",
    "uid": "05af78ac-a774-478c-a50c-8b9c234e071e",
    "side": "sell",
    "type": "fill",
    "seq": 653355,
    "time": 1612266317519,
    "qty": 15000,
    "price": 34969.5
}

TICKER_MSG = {
    "time": 1612270825253,
    "feed": "ticker",
    "product_id": "PI_XBTUSD",
    "bid": 34832.5,
    "ask": 34847.5,
    "bid_size": 42864,
    "ask_size": 2300,
    "volume": 262306237,
    "dtm": 0,
    "leverage": "50x",
    "index": 34803.45,
    "premium": 0.1,
    "last": 34852,
    "change": 2.995109121267192,
    "funding_rate": 3.891007752e-9,
    "funding_rate_prediction": 4.2233756e-9,
    "suspended": False,
    "tag": "perpetual",
    "pair": "XBT:USD",
    "openInterest": 107706940,
    "markPrice": 34844.25,
    "maturityTime": 0,
    "relative_funding_rate": 0.000135046879166667,
    "relative_funding_rate_prediction": 0.000146960125,
    "next_funding_rate_time": 1612281600000
}

FILLS_MSG = {
    "feed": "fills",
    "username": "DemoUser",
    "fills": [
        {
            "instrument": "PI_XBTUSD",
            "time": 1600256966528,
            "price": 364.65,
            "seq": 100,
            "buy": True,
            "qty": 5000.0,
            "order_id": "3696d19b-3226-46bd-993d-a9a7aacc8fbc",
            "cli_ord_id": "8b58d9da-fcaf-4f60-91bc-9973a3eba48d",
            "fill_id": "c14ee7cb-ae25-4601-853a-d0205e576099",
            "fill_type": "taker",
            "fee_paid": 0.00685588921,
            "fee_currency": "ETH"
        }
    ]
}

ORDERS_MSG = {
    'feed': 'open_orders',
    'order': {
        'instrument': 'PI_XBTUSD',
        'time': 1567702877410,
        'last_update_time': 1567702877410,
        'qty': 304.0,
        'filled': 0.0,
        'limit_price': 10640.0,
        'stop_price': 0.0,
        'type': 'limit',
        'order_id': '59302619-41d2-4f0b-941f-7e7914760ad3',
        'direction': 1,
        'reduce_only': True
    },
    'is_cancel': False,
    'reason': 'new_placed_order_by_user'
}


class TestKrakenFuturesWSClient(unittest.TestCase):
    """
    Unittest to test implementation of Kraken Futures websocket client
    """
    def setUp(self):
        self.client = KrakenFuturesWSClient({})

    def test_parse_orders_msg(self):
        (sub_key, order_update_event), = self.client._handle_feed_message(ORDERS_MSG)

        self.assertTrue(isinstance(order_update_event, OrderUpdateEvent))
        self.assertEqual(sub_key, 'open_orders')
        self.assertEqual(order_update_event.data.order_id, '59302619-41d2-4f0b-941f-7e7914760ad3')
        self.assertEqual(order_update_event.data.instrument, KRAKEN_TICKER_TO_INSTRUMENTS['PI_XBTUSD'])
        self.assertEqual(order_update_event.data.order_type, OrderType.LMT)
        self.assertEqual(order_update_event.data.side, OrderSide.SELL)
        self.assertEqual(order_update_event.data.status, OrderStatus.OPEN)
        self.assertEqual(order_update_event.data.size, 304.0)
        self.assertEqual(order_update_event.data.filled_size, 0.0)
        self.assertEqual(order_update_event.data.remaining_size, 304.0)
        self.assertTrue(np.isclose(order_update_event.data.avg_fill_price, np.nan, equal_nan=True))
        self.assertEqual(order_update_event.data.created_at, None)
        self.assertTrue(order_update_event.data.price, 10640.0)
        self.assertEqual(order_update_event.data.client_id, None)
        self.assertTrue(np.isclose(order_update_event.data.bid_price, np.nan, equal_nan=True))
        self.assertTrue(np.isclose(order_update_event.data.ask_price, np.nan, equal_nan=True))
        self.assertTrue(np.isclose(order_update_event.data.bid_size, np.nan, equal_nan=True))
        self.assertTrue(np.isclose(order_update_event.data.ask_size, np.nan, equal_nan=True))

    def test_parse_fills_msg(self):
        (sub_key, fills_event), = self.client._handle_feed_message(FILLS_MSG)

        self.assertTrue(isinstance(fills_event, FillEvent))
        self.assertEqual(sub_key, 'fills')
        self.assertEqual(fills_event.data.timestamp, 1600256966528 / 1000)
        self.assertEqual(fills_event.data.instrument, KRAKEN_TICKER_TO_INSTRUMENTS['PI_XBTUSD'])
        self.assertEqual(fills_event.data.order_id, "3696d19b-3226-46bd-993d-a9a7aacc8fbc")
        self.assertEqual(fills_event.data.fill_id, "c14ee7cb-ae25-4601-853a-d0205e576099")
        self.assertEqual(fills_event.data.trade_id, "8b58d9da-fcaf-4f60-91bc-9973a3eba48d")
        self.assertEqual(fills_event.data.side, 'buy')
        self.assertEqual(fills_event.data.price, 364.65)
        self.assertEqual(fills_event.data.size, 5000.0)
        self.assertEqual(fills_event.data.fill_type, 'taker')
        self.assertEqual(fills_event.data.fee, 0.00685588921)

    def test_parse_trades_msg(self):
        (sub_key, tick_event), = self.client._handle_feed_message(TRADES_MSG)

        self.assertTrue(isinstance(tick_event, TickEvent))
        self.assertEqual(sub_key, 'trade.PI_XBTUSD')
        self.assertEqual(tick_event.data.timestamp, 1612266317519 / 1000)
        self.assertEqual(tick_event.data.instrument, KRAKEN_TICKER_TO_INSTRUMENTS['PI_XBTUSD'])
        self.assertEqual(tick_event.data.trade_id, "05af78ac-a774-478c-a50c-8b9c234e071e")
        self.assertEqual(tick_event.data.price, 34969.5)
        self.assertEqual(tick_event.data.size, 15000)
        self.assertEqual(tick_event.data.side, 'sell')
        self.assertEqual(tick_event.data.liquidation, False)

    def test_parse_ticker_msg(self):
        (sub_key, quote_event), = self.client._handle_feed_message(TICKER_MSG)

        self.assertTrue(isinstance(quote_event, QuoteEvent))
        self.assertEqual(sub_key, 'ticker.PI_XBTUSD')
        self.assertEqual(quote_event.data.timestamp, 1612270825253 / 1000)
        self.assertEqual(quote_event.data.instrument, KRAKEN_TICKER_TO_INSTRUMENTS['PI_XBTUSD'])
        self.assertEqual(quote_event.data.bid, 34832.5)
        self.assertEqual(quote_event.data.bid_size, 42864)
        self.assertEqual(quote_event.data.ask, 34847.5)
        self.assertEqual(quote_event.data.ask_size, 2300)
        self.assertEqual(quote_event.data.last, 34852)


