from enum import Enum


class OrderType(Enum):
    MKT = "MKT"
    LMT = "LMT"

    def __str__(self):
        return '{}'.format(self.name)
