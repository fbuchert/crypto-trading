from enum import Enum


class OrderStatus(Enum):
    CREATED = "CREATED"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    ERROR = "ERROR"

    def __str__(self):
        return '{}'.format(self.name)
