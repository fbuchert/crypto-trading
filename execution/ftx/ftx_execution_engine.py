import os
import logging
import asyncio
import pandas as pd
from typing import Tuple, Dict, Optional, Callable

from core.trade import Trade
from core.events import EventType
from core.instrument import Instrument
from core.order_status import OrderStatus
from core.events import Event, OrderUpdateEvent, FillEvent, TradeExecutedEvent
from execution.ftx.market_trade import MarketTrade
from execution.base_execution_engine import BaseExecutionEngine

rootLogger = logging.getLogger()


class FTXExecutionEngine(BaseExecutionEngine):
    def __init__(self, name: str = 'ftx_execution_engine', save_path: Optional[str] = None):
        super().__init__(name, save_path)

    async def execute_trade(self, instrument: Instrument, size: float, exec_callback: Callable):
        trade = MarketTrade(instrument, size, self.api_client, exec_callback)

        try:
            await trade.start()
            self.active_trades[trade.order_id] = trade
        except Exception as e:
            rootLogger.info(f'Exception during start of order execution: {e}.')

    def handle_event(self, event: Event):
        try:
            if event.type is EventType.ORDER_UPDATED:
                asyncio.create_task(self._handle_order_data(event))
            elif event.type == EventType.FILL:
                asyncio.create_task(self._handle_fill_data(event))
        except Exception as e:
            rootLogger.error(f'Error in handle_event function in execution engine: {e}')

    async def _handle_order_data(self, event: OrderUpdateEvent) -> None:
        if event.data.order_id not in self.active_trades.keys():
            return
        trade = self.active_trades[event.data.order_id]
        await trade.handle_order_update(event)

        if trade.order_status == OrderStatus.CLOSED:
            rootLogger.info(f'Order {trade} closed. Updating data structures and saving order event sequence.')
            trade = self.active_trades.pop(trade.order_id)

            trade.execution_callback(TradeExecutedEvent(trade, self.name))
            if self.save_order_event_dicts:
                asyncio.create_task(asyncio.to_thread(self._save_order_sequence, trade))
        elif trade.order_status == OrderStatus.ERROR:
            # Removing trade from data structures. Trade / order failure should be investigated.
            _ = self.active_trades.pop(trade.order_id)
            raise ValueError(f'Order {trade} is in error state.')

    async def _handle_fill_data(self, event: FillEvent) -> None:
        pass

    def _save_order_sequence(self, trade: Trade):
        event_dict_list = list(map(lambda event: event.as_dict(), trade.trade_events))
        df = pd.DataFrame(event_dict_list)
        file_name = '{}_{}.csv'.format(pd.Timestamp(df['timestamp'].iloc[0]).value, trade.order_id)
        df.to_csv(os.path.join(self.save_path, file_name))
