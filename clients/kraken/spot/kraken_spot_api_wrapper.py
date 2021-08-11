from clients.api_client_base import APIClientBase
from clients.kraken.spot.kraken_spot_api import KrakenSpotAPIClient


class KrakenSpotAPIWrapper(APIClientBase, KrakenSpotAPIClient):
    def __init__(self, api_keys, exchange_id='kraken_spot'):
        APIClientBase.__init__(self, exchange_id)
        KrakenSpotAPIClient.__init__(self, api_keys['key'], api_keys['secret'])

    def get_account(self):
        return self.query_private('Balance')

    def get_positions(self):
        self.query_private('OpenPositions')

    def get_instrument_quotes(self, instrument_id: str, depth: int = 1):
        res = self.query_public('Depth', {'pair': instrument_id, 'count': depth})['result']
        bids = list(map(lambda x: {'symbol': instrument_id, 'side': 'buy', 'size': x[1], 'price': x[0]}, res[instrument_id]['bids']))
        asks = list(map(lambda x: {'symbol': instrument_id, 'side': 'sell', 'size': x[1], 'price': x[0]}, res[instrument_id]['asks']))
        return bids, asks

    def buy_market(self, instrument_id: str, size: float):
        return self.query_private(
            method='AddOrder',
            data={
                'orderType': 'market',
                'type': 'buy',
                'pair': instrument_id,
                'volume': size
            }
        )

    def sell_market(self, instrument_id: str, size: float):
        return self.query_private(
            method='AddOrder',
            data={
                'orderType': 'market',
                'type': 'sell',
                'pair': instrument_id,
                'volume': size
            }
        )

    def buy_limit(self, instrument_id: str, lmt_price: float, size: float):
        return self.query_private(
            method='AddOrder',
            data={
                'orderType': 'limit',
                'type': 'buy',
                'pair': instrument_id,
                'volume': size,
                'price': lmt_price
            }
        )

    def sell_limit(self, instrument_id: str, lmt_price: float, size: float):
        return self.query_private(
            method='AddOrder',
            data={
                'orderType': 'limit',
                'type': 'sell',
                'pair': instrument_id,
                'volume': size,
                'price': lmt_price
            }
        )

    def cancel_order_by_id(self, order_id: str):
        return self.query_private(
            method='CancelOrder',
            data={
                'txid': order_id
            }
        )
