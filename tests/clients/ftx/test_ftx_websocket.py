import unittest

import numpy as np
from core.const import FTX_TICKER_TO_INSTRUMENTS
from core.order_type import OrderType
from core.order_status import OrderStatus
from core.order_side import OrderSide
from core.events import FillEvent, TickEvent, OrderUpdateEvent, QuoteEvent
from clients.ftx.ftx_websocket import FTXWebsocketClient

TRADES_MSG = {
    'channel': 'trades',
    'market': 'BTC-PERP',
    'type': 'update',
    'data': [
        {
            'id': 1468501329,
            'price': 31708.0,
            'size': 0.0786,
            'side': 'sell',
            'liquidation': False,
            'time': '2021-07-21T20:49:12.908392+00:00'
        },
        {
            'id': 1468501569,
            'price': 31710.0,
            'size': 0.0536,
            'side': 'buy',
            'liquidation': False,
            'time': '2021-07-21T20:50:12.908392+00:00'
        }
    ]
}

TICKER_MSG = {
    'channel': 'ticker',
    'market': 'BTC-PERP',
    'type': 'update',
    'data': {
        'bid': 31708.0,
        'ask': 31709.0,
        'bidSize': 18.0695,
        'askSize': 1.7919,
        'last': 31708.0,
        'time': 1626900552.9121816
    }
}

FILLS_MSG = {
    'channel': 'fills',
    'type': 'update',
    'data': {
        'id': 2958651259,
        'market': 'BTC-PERP',
        'future': 'BTC-PERP',
        'baseCurrency': None,
        'quoteCurrency': None,
        'type': 'order',
        'side': 'buy',
        'price': 31699.0,
        'size': 0.0002,
        'orderId': 65376379322,
        'time': '2021-07-21T20:53:04.467458+00:00',
        'tradeId': 1468513163,
        'feeRate': 0.0007,
        'fee': 0.00443786,
        'feeCurrency': 'USD',
        'liquidity': 'taker'
    }
}

ORDERS_MSG = {
    'channel': 'orders',
    'type': 'update',
    'data': {
        'id': 65376379322,
        'clientId': None,
        'market': 'BTC-PERP',
        'type': 'market',
        'side': 'buy',
        'price': None,
        'size': 0.0002,
        'status': 'closed',
        'filledSize': 0.0002,
        'remainingSize': 0.0,
        'reduceOnly': False,
        'liquidation': False,
        'avgFillPrice': 31699.0,
        'postOnly': False,
        'ioc': True,
        'createdAt': '2021-07-21T20:53:04.414013+00:00'
    }
}


class TestFTXWebsocketClient(unittest.TestCase):
    """
    Unittest to test implementation of FTX websocket client
    """
    def setUp(self):
        self.client = FTXWebsocketClient({})

    def test_parse_orders_msg(self):
        (sub_key, order_update_event), = self.client._handle_feed_message(ORDERS_MSG)

        self.assertTrue(isinstance(order_update_event, OrderUpdateEvent))
        self.assertEqual(sub_key, 'orders')
        self.assertEqual(order_update_event.data.order_id, 65376379322)
        self.assertEqual(order_update_event.data.instrument, FTX_TICKER_TO_INSTRUMENTS['BTC-PERP'])
        self.assertEqual(order_update_event.data.order_type, OrderType.MKT)
        self.assertEqual(order_update_event.data.side, OrderSide.BUY)
        self.assertEqual(order_update_event.data.status, OrderStatus.CLOSED)
        self.assertEqual(order_update_event.data.size, 0.0002)
        self.assertEqual(order_update_event.data.filled_size, 0.0002)
        self.assertEqual(order_update_event.data.remaining_size, 0.0)
        self.assertEqual(order_update_event.data.avg_fill_price, 31699.0)
        self.assertEqual(order_update_event.data.created_at, 1626900784.414013)
        self.assertTrue(np.isclose(order_update_event.data.price, np.nan, equal_nan=True))
        self.assertEqual(order_update_event.data.client_id, None)
        self.assertTrue(np.isclose(order_update_event.data.bid_price, np.nan, equal_nan=True))
        self.assertTrue(np.isclose(order_update_event.data.ask_price, np.nan, equal_nan=True))
        self.assertTrue(np.isclose(order_update_event.data.bid_size, np.nan, equal_nan=True))
        self.assertTrue(np.isclose(order_update_event.data.ask_size, np.nan, equal_nan=True))

    def test_parse_fills_msg(self):
        (sub_key, fills_event), = self.client._handle_feed_message(FILLS_MSG)

        self.assertTrue(isinstance(fills_event, FillEvent))
        self.assertEqual(sub_key, 'fills')
        self.assertEqual(fills_event.data.timestamp, 1626900784.467458)
        self.assertEqual(fills_event.data.instrument, FTX_TICKER_TO_INSTRUMENTS['BTC-PERP'])
        self.assertEqual(fills_event.data.order_id, 65376379322)
        self.assertEqual(fills_event.data.fill_id, 2958651259)
        self.assertEqual(fills_event.data.trade_id, 1468513163)
        self.assertEqual(fills_event.data.side, 'buy')
        self.assertEqual(fills_event.data.price, 31699.0)
        self.assertEqual(fills_event.data.size, 0.0002)
        self.assertEqual(fills_event.data.fill_type, 'taker')
        self.assertEqual(fills_event.data.fee_rate, 0.0007)
        self.assertEqual(fills_event.data.fee, 0.00443786)

    def test_parse_trades_msg(self):
        (sub_key, tick_event), _ = self.client._handle_feed_message(TRADES_MSG)

        self.assertTrue(isinstance(tick_event, TickEvent))
        self.assertEqual(sub_key, 'trades.BTC-PERP')
        self.assertEqual(tick_event.data.timestamp, 1626900552.908392)
        self.assertEqual(tick_event.data.instrument, FTX_TICKER_TO_INSTRUMENTS['BTC-PERP'])
        self.assertEqual(tick_event.data.trade_id, 1468501329)
        self.assertEqual(tick_event.data.price, 31708.0)
        self.assertEqual(tick_event.data.size, 0.0786)
        self.assertEqual(tick_event.data.side, 'sell')
        self.assertEqual(tick_event.data.liquidation, False)

    def test_parse_ticker_msg(self):
        (sub_key, quote_event), = self.client._handle_feed_message(TICKER_MSG)

        self.assertTrue(isinstance(quote_event, QuoteEvent))
        self.assertEqual(sub_key, 'ticker.BTC-PERP')
        self.assertEqual(quote_event.data.timestamp, 1626900552.9121816)
        self.assertEqual(quote_event.data.instrument, FTX_TICKER_TO_INSTRUMENTS['BTC-PERP'])
        self.assertEqual(quote_event.data.bid, 31708.0)
        self.assertEqual(quote_event.data.bid_size, 18.0695)
        self.assertEqual(quote_event.data.ask, 31709.0)
        self.assertEqual(quote_event.data.ask_size, 1.7919)
        self.assertEqual(quote_event.data.last, 31708.0)

    def test_bar_roll(self):
        # Manually initialize bar variable and subscription for test
        self.client._initialize_bar_variables(FTX_TICKER_TO_INSTRUMENTS['BTC-PERP'], '1m')
        event_list = self.client._handle_feed_message(TRADES_MSG)

        # We expect 4 update events: two TickEvents (trades) and two BarEvents (updates of minute bar)
        self.assertEqual(len(event_list), 4)

        # Check that bar timestamp has been rolled
        (_, bar_event_1), (_, bar_event_2) = event_list[-2:]
        self.assertEqual(bar_event_1.data.timestamp, 1626900540)
        self.assertEqual(bar_event_2.data.timestamp, 1626900600)


