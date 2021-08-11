import numpy as np
from typing import Dict
from datetime import datetime

from core.instrument import Instrument


class Fill:
    def __init__(
            self,
            timestamp: float,
            instrument: Instrument,
            order_id: int,
            fill_id: int,
            trade_id: int,
            side: str,
            price: float,
            size: float,
            fill_type: str,
            fee_rate: float,
            fee: float
    ):
        self.timestamp = timestamp
        self.instrument = instrument
        self.order_id = order_id
        self.fill_id = fill_id
        self.trade_id = trade_id
        self.side = side
        self.price = price
        self.size = size
        self.fill_type = fill_type
        self.fee_rate = fee_rate
        self.fee = fee

    @classmethod
    def from_ftx_msg(cls, instrument: Instrument, msg: Dict):
        return cls(
            datetime.fromisoformat(msg['data']['time']).timestamp(),
            instrument,
            msg['data']['orderId'],
            msg['data']['id'],
            msg['data']['tradeId'],
            msg['data']['side'],
            msg['data']['price'],
            msg['data']['size'],
            msg['data']['liquidity'],
            msg['data']['feeRate'],
            msg['data']['fee']
        )

    @classmethod
    def from_kraken_fut_msg(cls, instrument, msg: Dict):
        return cls(
            msg['time'] / 1000,
            instrument,
            msg['order_id'],
            msg['fill_id'],
            msg['cli_ord_id'],
            'buy' if msg['buy'] else 'sell',
            msg['price'],
            msg['qty'],
            msg['fill_type'],
            np.nan,
            msg['fee_paid']
        )
