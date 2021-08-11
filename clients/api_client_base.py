from abc import ABC, abstractmethod


class APIClientBase(ABC):
    def __init__(self, exchange_id: str):
        if not isinstance(exchange_id, str):
            raise AttributeError("Initialization of exchange module failed. Invalid exchange name format: {}".format(exchange_id))
        self.exchange_id = exchange_id

    @abstractmethod
    def get_account(self):
        pass

    @abstractmethod
    def get_positions(self):
        pass

    @abstractmethod
    def get_instrument_quotes(self, instrument_id: str, depth: int = 1):
        pass

    @abstractmethod
    def buy_market(self, instrument_id: str, size: float):
        pass

    @abstractmethod
    def sell_market(self, instrument_id: str, size: float):
        pass

    @abstractmethod
    def buy_limit(self, instrument_id: str, lmt_price: float, size: float):
        pass

    @abstractmethod
    def sell_limit(self, instrument_id: str, lmt_price: float, size: float):
        pass

    @abstractmethod
    def cancel_order_by_id(self, order_id: str):
        pass
