import unittest

import numpy as np
from core.const import KRAKEN_TICKER_TO_INSTRUMENTS
from core.events import TickEvent, QuoteEvent
from clients.kraken.spot.kraken_spot_ws import KrakenSpotWSClient

# Ticker / quotes are called spread on the kraken spot exchange
TICKER_MSG = [
    0,
    [
        "5698.40000",
        "5700.00000",
        "1542057299.545897",
        "1.01234567",
        "0.98765432"
    ],
    "spread",
    "XBT/USD"
]


TRADE_MSG = [
    0,
    [
        [
            "5541.20000",
            "0.15850568",
            "1534614057.321597",
            "s",
            "l",
            ""
        ],
        [
            "6060.00000",
            "0.02455000",
            "1534614057.324998",
            "b",
            "l",
            ""
        ]
    ],
    "trade",
    "XBT/USD"
]


class TestKrakenSpotWSClient(unittest.TestCase):
    """
    Unittest to test implementation of Kraken Futures websocket client
    """
    def setUp(self):
        self.client = KrakenSpotWSClient({})

    def test_parse_trades_msg(self):
        (sub_key, tick_event_1), (sub_key, tick_event_2) = self.client._handle_feed_message(TRADE_MSG)

        # Test correctness of first trade / tick event
        self.assertTrue(isinstance(tick_event_1, TickEvent))
        self.assertEqual(sub_key, 'trade.XBT/USD')
        self.assertEqual(tick_event_1.data.timestamp, 1534614057.321597)
        self.assertEqual(tick_event_1.data.instrument, KRAKEN_TICKER_TO_INSTRUMENTS['XBT/USD'])
        self.assertEqual(tick_event_1.data.trade_id, None)
        self.assertEqual(tick_event_1.data.price, 5541.20000)
        self.assertEqual(tick_event_1.data.size, 0.15850568)
        self.assertEqual(tick_event_1.data.side, 'sell')
        self.assertEqual(tick_event_1.data.liquidation, None)

        # Test correctness of second trade / tick event
        self.assertTrue(isinstance(tick_event_2, TickEvent))
        self.assertEqual(sub_key, 'trade.XBT/USD')
        self.assertEqual(tick_event_2.data.timestamp, 1534614057.324998)
        self.assertEqual(tick_event_2.data.instrument, KRAKEN_TICKER_TO_INSTRUMENTS['XBT/USD'])
        self.assertEqual(tick_event_2.data.trade_id, None)
        self.assertEqual(tick_event_2.data.price, 6060.00000)
        self.assertEqual(tick_event_2.data.size, 0.02455000)
        self.assertEqual(tick_event_2.data.side, 'buy')
        self.assertEqual(tick_event_2.data.liquidation, None)

    def test_parse_ticker_msg(self):
        (sub_key, quote_event), = self.client._handle_feed_message(TICKER_MSG)

        self.assertTrue(isinstance(quote_event, QuoteEvent))
        self.assertEqual(sub_key, 'spread.XBT/USD')
        self.assertEqual(quote_event.data.timestamp, 1542057299.545897)
        self.assertEqual(quote_event.data.instrument, KRAKEN_TICKER_TO_INSTRUMENTS['XBT/USD'])
        self.assertEqual(quote_event.data.bid, 5698.40000)
        self.assertEqual(quote_event.data.bid_size, 1.01234567)
        self.assertEqual(quote_event.data.ask, 5700.00000)
        self.assertEqual(quote_event.data.ask_size, 0.98765432)
        self.assertTrue(np.isclose(quote_event.data.last, np.nan, equal_nan=True))
