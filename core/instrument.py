
class Instrument:
    def __init__(
            self,
            name: str,
            instrument_id: str,
            tick_size: float,
            size_unit: float
    ):
        self.name = name
        self.instrument_id = instrument_id
        self.tick_size = tick_size
        self.size_unit = size_unit
