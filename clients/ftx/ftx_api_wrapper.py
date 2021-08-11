from typing import Dict
from clients.api_client_base import APIClientBase
from clients.ftx.ftx_api import FTXClient


class FTXClientWrapper(APIClientBase, FTXClient):
    def __init__(self, api_keys: Dict, exchange_id: str = 'ftx', subaccount: str = None):
        APIClientBase.__init__(self, exchange_id)
        FTXClient.__init__(self, api_keys['key'], api_keys['secret'], subaccount_name=subaccount)

    def get_account(self):
        return FTXClient.get_account_info(self)

    def get_positions(self):
        return FTXClient.get_positions(self)

    def get_instrument_quotes(self, instrument_id: str, depth: int = 1):
        order_book = self.get_orderbook(instrument_id, depth)
        bids = list(map(lambda x: {'symbol': instrument_id, 'side': 'buy', 'size': x[1], 'price': x[0]},
                    order_book['bids']))
        asks = list(map(lambda x: {'symbol': instrument_id, 'side': 'sell', 'size': x[1], 'price': x[0]},
                    order_book['asks']))
        return bids, asks

    def buy_market(self, instrument_id: str, size: float):
        return self.place_order(market=instrument_id, side='buy', price=0.0, size=size, type='market')

    def sell_market(self, instrument_id: str, size: float):
        return self.place_order(market=instrument_id, side='sell', price=0.0, size=size, type='market')

    def buy_limit(self, instrument_id: str, lmt_price: float, size: float):
        return self.place_order(market=instrument_id, side='buy', price=lmt_price, size=size, type='limit')

    def sell_limit(self, instrument_id: str, lmt_price: float, size: float):
        return self.place_order(market=instrument_id, side='sell', price=lmt_price, size=size, type='limit')

    def modify_order(self, order_id: str, lmt_price: float = None, new_size: float = None):
        return self._modify_order(existing_order_id=order_id, price=lmt_price, size=new_size)

    def cancel_order_by_id(self, order_id: str):
        return self.cancel_order(order_id)
