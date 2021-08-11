from enum import Enum


class EventType(Enum):
    # Data data streams
    ORDER = "ORDER"
    FILL = "FILL"
    TICK = "TRADE"
    QUOTE = "QUOTE"
    BAR = "BAR"

    # Order execution stream
    ORDER_UPDATED = "ORDER_UPDATED"

    TRADE_EXECUTED = "ORDER_EXECUTED"
