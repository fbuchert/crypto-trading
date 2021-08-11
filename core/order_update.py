import numpy as np
from datetime import datetime
from typing import Optional, Union, Dict
from core.order_type import OrderType
from core.order_side import OrderSide
from core.order_status import OrderStatus
from core.instrument import Instrument


class OrderUpdate:
    def __init__(
            self,
            timestamp: float,
            order_id: Union[int, str],
            instrument: Instrument,
            order_type: OrderType,
            side: OrderSide,
            status: OrderStatus,
            size: float,
            filled_size: float,
            remaining_size: float,
            avg_fill_price: Optional[float] = np.nan,
            created_at: Optional[float] = None,
            price: float = np.nan,
            client_id: Union[str, int, None] = None,
            bid_price: float = np.nan,
            bid_size: float = np.nan,
            ask_price: float = np.nan,
            ask_size: float = np.nan
    ):
        self.timestamp = timestamp
        self.order_id = order_id
        self.instrument = instrument
        self.order_type = order_type
        self.side = side
        self.status = status
        self.size = size
        self.filled_size = filled_size
        self.remaining_size = remaining_size
        self.avg_fill_price = avg_fill_price
        self.created_at = created_at
        self.price = price
        self.client_id = client_id
        self.bid_price = bid_price
        self.bid_size = bid_size
        self.ask_price = ask_price
        self.ask_size = ask_size

    def as_dict(self) -> Dict[str, Union[str, int, float, None]]:
        return {
            'timestamp': self.timestamp,
            'order_id': self.order_id,
            'instrument': self.instrument.name,
            'order_type': self.order_type.__str__(),
            'side': self.side.__str__(),
            'status': self.status.__str__(),
            'size': self.size,
            'filled_size': self.filled_size,
            'remaining_size': self.remaining_size,
            'avg_fill_price': self.avg_fill_price,
            'created_at': self.created_at,
            'price': self.price,
            'client_id': self.client_id,
            'bid_price': self.bid_price,
            'bid_size': self.bid_size,
            'ask_price': self.ask_price,
            'ask_size': self.ask_size
        }

    @classmethod
    def from_ftx_msg(cls, instrument: Instrument, msg_data: Dict, bid_dict: Dict = None, ask_dict: Dict = None):
        order_type = OrderType.MKT if msg_data['type'] == 'market' else OrderType.LMT
        side = OrderSide.BUY if msg_data['side'] == 'buy' else OrderSide.SELL

        if msg_data['status'] == 'new':
            status = OrderStatus.CREATED
        elif msg_data['status'] == 'closed':
            status = OrderStatus.CLOSED
        elif msg_data['status'] == 'open':
            status = OrderStatus.OPEN
        else:
            status = OrderStatus.ERROR

        return cls(
            datetime.utcnow().timestamp(),
            msg_data['id'],
            instrument,
            order_type,
            side,
            status,
            msg_data['size'],
            msg_data['filledSize'],
            msg_data['remainingSize'],
            msg_data['avgFillPrice'],
            datetime.fromisoformat(msg_data['createdAt']).timestamp(),
            msg_data['price'] if msg_data['price'] is not None else np.nan,
            msg_data['clientId'],
            bid_price=bid_dict['price'] if bid_dict is not None else np.nan,
            bid_size=bid_dict['size'] if bid_dict is not None else np.nan,
            ask_price=ask_dict['price'] if ask_dict is not None else np.nan,
            ask_size=ask_dict['size'] if ask_dict is not None else np.nan
        )

    @classmethod
    def from_kraken_fut_msg(cls, instrument: Instrument, msg: Dict, reason: Optional[str] = None):
        order_type = OrderType.MKT if msg['type'] == 'market' else OrderType.LMT
        side = OrderSide.BUY if msg['direction'] == 0 else OrderSide.SELL

        if reason is None:
            # No reason means this is a snapshot message, i.e. the order is open.
            order_status = OrderStatus.OPEN
        elif reason == 'new_order_placed_by_user':
            order_status = OrderStatus.CREATED
        elif reason == 'full_fill':
            order_status = OrderStatus.CLOSED
        else:
            # Other order update reasons are not supported yet.
            order_status = OrderStatus.ERROR

        return cls(
            msg['time'],
            msg['order_id'],
            instrument,
            order_type,
            side,
            order_status,
            msg['qty'],
            msg['filled'],
            msg['qty'] - msg['filled'],
            price=msg['limit_price']
        )
