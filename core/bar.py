from core.instrument import Instrument
from utils.timedelta_parser import convert_to_timedelta


class Bar:
    def __init__(self, instrument: Instrument, freq: str):
        self.instrument = instrument
        self.freq = freq
        self.norm_seconds = convert_to_timedelta(freq).total_seconds()

        self.timestamp = None
        self.open = None
        self.high = None
        self.low = None
        self.close = None
        self.volume = 0

    def reset(self):
        self.timestamp = None
        self.open = None
        self.high = None
        self.low = None
        self.close = None
        self.volume = 0

    def update_bar(self, timestamp: float, price: float, size: float) -> None:
        if self.timestamp is None:
            self.timestamp = (timestamp // self.norm_seconds) * self.norm_seconds
        if self.open is None:
            self.open = price
        self.high = max(self.high, price) if self.high is not None else price
        self.low = min(self.low, price) if self.low is not None else price
        self.close = price
        self.volume += size

    def is_complete(self, timestamp: float) -> bool:
        if self.timestamp is None:
            return False
        else:
            return (timestamp // self.norm_seconds) > (self.timestamp // self.norm_seconds)
