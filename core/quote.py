import numpy as np
from typing import Dict, List
from datetime import datetime

from core.instrument import Instrument


class Quote(object):
    def __init__(
            self,
            timestamp: float,
            instrument: Instrument,
            bid: float,
            bid_size: float,
            ask: float,
            ask_size: float,
            last: float
    ):
        self.timestamp = timestamp
        self.instrument = instrument
        self.bid = bid
        self.bid_size = bid_size
        self.ask = ask
        self.ask_size = ask_size
        self.last = last

    @classmethod
    def from_ftx_msg(cls, instrument: Instrument, msg: Dict):
        return cls(
            msg['data']['time'],
            instrument,
            msg['data']['bid'],
            msg['data']['bidSize'],
            msg['data']['ask'],
            msg['data']['askSize'],
            msg['data']['last']
        )

    @classmethod
    def from_kraken_fut_msg(cls, instrument: Instrument, msg: Dict):
        return cls(
            msg['time'] / 1000,
            instrument,
            msg['bid'],
            msg['bid_size'],
            msg['ask'],
            msg['ask_size'],
            msg['last']
        )

    @classmethod
    def from_kraken_spot_msg(cls, instrument: Instrument, msg: List):
        return cls(
            float(msg[1][2]),
            instrument,
            float(msg[1][0]),
            float(msg[1][3]),
            float(msg[1][1]),
            float(msg[1][4]),
            np.nan
        )
