from core.instrument import Instrument


def get_rounded_size(size: float, instrument: Instrument) -> float:
    return round(round(size / instrument.size_unit) * instrument.size_unit, 8)
