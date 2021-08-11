import unittest
from unittest.mock import Mock

import numpy as np
from core.instrument import Instrument
from core.trade import Trade
from core.events import TradeExecutedEvent
from portfolio.portfolio import Portfolio


class TestPortfolio(unittest.TestCase):
    """
    Unittest to test implementation of portfolio class
    """
    def setUp(self):
        self._instruments = [
            Instrument(name='btc_usd_perp', instrument_id='BTC-PERP', tick_size=1, size_unit=0.0001),
            Instrument(name='eth_usd_perp', instrument_id='ETH-PERP', tick_size=0.01, size_unit=0.001),
            Instrument(name='ltc_usd_perp', instrument_id='LTC-PERP', tick_size=0.01, size_unit=0.01)
        ]

    def test_init(self):
        portfolio = Portfolio(self._instruments)

        current_position = portfolio.get_current_position()
        self.assertEqual(len(current_position), 3, 'Length of position array is not equal number of specified instruments.')
        self.assertEqual(current_position.index.tolist(), ['btc_usd_perp', 'eth_usd_perp', 'ltc_usd_perp'])
        self.assertEqual(current_position.tolist(), [0, 0, 0])

    def test_handle_execution(self):
        portfolio = Portfolio(self._instruments)

        trade = Trade(self._instruments[0], size=1.0, client=Mock(), execution_callback=Mock())
        trade_executed_event = TradeExecutedEvent(trade)
        portfolio.handle_execution(trade_executed_event)
        self.assertEqual(portfolio.get_current_position()[self._instruments[0].name], 1.0)

        trade = Trade(self._instruments[1], -1.0, client=Mock(), execution_callback=Mock())
        trade_executed_event = TradeExecutedEvent(trade)
        portfolio.handle_execution(trade_executed_event)
        self.assertEqual(portfolio.get_current_position()[self._instruments[1].name], -1.0)

        trade = Trade(self._instruments[0], -1.0, client=Mock(), execution_callback=Mock())
        trade_executed_event = TradeExecutedEvent(trade)
        portfolio.handle_execution(trade_executed_event)
        self.assertEqual(portfolio.get_current_position()[self._instruments[0].name], 0.0)


if __name__ == '__main__':
    unittest.main()
