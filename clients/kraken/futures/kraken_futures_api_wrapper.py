from typing import Dict
from clients.api_client_base import APIClientBase
from clients.kraken.futures.kraken_futures_api import KrakenFuturesAPIClient


class KrakenFuturesAPIWrapper(APIClientBase, KrakenFuturesAPIClient):
    def __init__(self, api_keys: Dict, exchange_id: str = 'kraken_futures_api', timeout: int = 10, check_certificate: bool = True):
        APIClientBase.__init__(self, exchange_id)
        KrakenFuturesAPIClient.__init__(self, api_keys, timeout=timeout, checkCertificate=check_certificate)

    def get_account(self):
        return self.get_accounts()

    def get_positions(self):
        return self.get_openpositions()

    def get_instrument_quotes(self, instrument_id: str, depth: int = 1):
        orderBook = self.get_orderbook(instrument_id)
        bids = list(map(lambda x: {'symbol': instrument_id, 'side': 'buy', 'size': x[1], 'price': x[0]}, orderBook["orderBook"]["bids"][:depth]))
        asks = list(map(lambda x: {'symbol': instrument_id, 'side': 'sell', 'size': x[1], 'price': x[0]}, orderBook["orderBook"]["asks"][:depth]))
        return bids, asks

    def buy_market(self, instrument_id: str, size: float):
        return self.send_order("mkt", instrument_id, "buy", abs(size))

    def sell_market(self, instrument_id: str, size: float):
        return self.send_order("mkt", instrument_id, "sell", abs(size))

    def buy_limit(self, instrument_id: str, lmt_price: float, size: float):
        return self.send_order("lmt", instrument_id, "buy", abs(size), lmt_price)

    def sell_limit(self, instrument_id: str, lmt_price: float, size: float):
        return self.send_order("lmt", instrument_id, "sell", abs(size), lmt_price)

    def cancel_order_by_id(self, order_id: str):
        return self.cancel_order(order_id=order_id)
