from datetime import datetime
from typing import Dict, Optional, List

from core.instrument import Instrument


class Tick(object):
    def __init__(
            self,
            timestamp: float,
            instrument: Instrument,
            trade_id: Optional[int],
            price: float,
            size: float,
            side: str,
            liquidation: Optional[bool]
    ):
        self.timestamp = timestamp
        self.instrument = instrument
        self.trade_id = trade_id
        self.price = price
        self.size = size
        self.side = side
        self.liquidation = liquidation

    @classmethod
    def from_ftx_msg(cls, instrument: Instrument, trade_msg: Dict):
        return cls(
            datetime.fromisoformat(trade_msg['time']).timestamp(),
            instrument,
            trade_msg['id'],
            trade_msg['price'],
            trade_msg['size'],
            trade_msg['side'],
            trade_msg['liquidation']
        )

    @classmethod
    def from_kraken_fut_msg(cls, instrument: Instrument, msg: Dict):
        return cls(
            msg['time'] / 1000,
            instrument,
            msg['uid'],
            msg['price'],
            msg['qty'],
            msg['side'],
            msg['type'] == 'liquidation'
        )

    @classmethod
    def from_kraken_spot_msg(cls, instrument: Instrument, msg: List):
        return cls(
            float(msg[2]),
            instrument,
            None,
            float(msg[0]),
            float(msg[1]),
            'buy' if msg[3] == 'b' else 'sell',
            None
        )
