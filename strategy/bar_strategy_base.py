import asyncio
import logging
import pandas as pd
from abc import ABC, abstractmethod

from typing import Dict, List, Optional

from portfolio.portfolio import Portfolio
from clients.websocket_base import WebsocketBase
from clients.api_client_base import APIClientBase
from execution.base_execution_engine import BaseExecutionEngine

from core.instrument import Instrument
from core.events import Event, EventType, BarEvent, TradeExecutedEvent

rootLogger = logging.getLogger()


class BarStrategyBase(ABC):
    def __init__(self, config: Dict, strategy_name: str):
        super().__init__()

        # General settings
        self.strategy_name: str = strategy_name
        self._instruments: List[Instrument] = config['instruments']
        self._strategy_params: Dict = config['strategy_params']
        self._trading_volume: float = config['trading_volume']  # Total value to trade volume in USD

        # API keys and initialization of exchange clients
        self._api_keys: Dict = config['exchange']['api_keys']
        if 'subaccount' in config['exchange'].keys():
            self._api_client: APIClientBase = config['exchange']['api_client'](api_keys=self._api_keys, subaccount=config['exchange']['subaccount'])
        else:
            self._api_client: APIClientBase = config['exchange']['api_client'](api_keys=self._api_keys)

        self._websocket_client: WebsocketBase = config['exchange']['websocket_client'](
            api_keys=self._api_keys,
            subaccount=config['exchange']['subaccount']
        )

        # Initialize portfolio manager and execution engine
        self._portfolio_manager: Portfolio = config['portfolio_manager'](
             self._instruments,
             save_path=config['position_save_path']
        )
        self._execution_engine: BaseExecutionEngine = config['execution_engine'](save_path=config['execution_save_path'])
        self._execution_engine.set_api_client(self._api_client)
        self._execution_engine.set_ws_client(self._websocket_client)

        # Initialize class_variables to store price data
        self._price_dfs: Dict[str, pd.DataFrame] = {}
        self._price_df_rolled: Dict[str, bool] = {instrument.name: False for instrument in self._instruments}
        self._last_roll_ts: Optional[pd.Timestamp] = None

    async def start(self) -> None:
        asyncio.create_task(self._websocket_client.start())
        while not self._websocket_client.is_running:
            await asyncio.sleep(0.1)

        asyncio.create_task(self._execution_engine.start())
        await self._subscribe_data_streams()

    async def close(self):
        await self._execution_engine.close()
        await self._websocket_client.close()

    async def _subscribe_data_streams(self) -> None:
        await asyncio.gather(
            *(
                self._websocket_client.subscribe_bars(
                    instrument=instrument,
                    consumer=self,
                    freq=self._strategy_params['bar_freq']
                )
                for instrument in self._instruments
            )
        )

    def _get_historical_price_data(self) -> None:
        raise NotImplementedError('Loading of historical price data is not supported yet.')

    def handle_event(self, event: Event) -> None:
        try:
            if isinstance(event, BarEvent):
                self._handle_bar_update(event)
            elif isinstance(event, TradeExecutedEvent):
                self._handle_execution(event)
            else:
                raise ValueError(f'Received event with unknown key in {self.strategy_name}-strategy.')
        except Exception as e:
            rootLogger.error(f'Error in handle_event method of {self.strategy_name}-strategy: {e}')

    def _handle_bar_update(self, event: BarEvent) -> None:
        self._update_price_dfs(event)

        if any(self._price_df_rolled.values()) and self._do_rebalance(event):
            self._last_roll_ts = pd.Timestamp(event.data.timestamp, unit='s', tz='utc')
            self._price_df_rolled = {instrument.name: False for instrument in self._instruments}
            rootLogger.info("Candle rolled: {}".format(self._last_roll_ts))

            # Get last common timestamp of all price dataframes
            last_ts = min([v.index[-1] for v in self._price_dfs.values()])
            price_dfs = {k: v.loc[:last_ts] for k, v in self._price_dfs.items()}

            # Calculate position
            target_position = self._calculate_target_position(price_dfs)
            target_position = (target_position * self._trading_volume)

            self._place_trades(target_position, price_dfs)

    def _place_trades(self, target_position: pd.Series, price_dfs: Dict[str, pd.DataFrame]) -> None:
        last_prices = pd.Series({k: price_dfs[k]['close'].iloc[-1] for k in target_position.keys()})
        position_deltas = target_position / last_prices - self._portfolio_manager.get_current_position()

        rootLogger.info('Target position {}'.format(target_position))
        rootLogger.info('Initiating execution of position deltas: {}'.format(position_deltas))
        for instrument in self._instruments:
            position_delta = position_deltas.loc[instrument.name]
            if position_delta != 0:
                asyncio.create_task(
                    self._execution_engine.execute_trade(
                        instrument=instrument,
                        size=position_delta,
                        exec_callback=self.handle_event)
                )

    def _handle_execution(self, event: TradeExecutedEvent):
        self._portfolio_manager.handle_execution(event)

    def _do_rebalance(self, event: BarEvent) -> bool:
        if self._last_roll_ts is None:
            return True

        # Only rebalance if difference between current event timestamp and last roll timestamp is larger than bar_freq
        ts_delta = pd.Timestamp(event.data.timestamp, unit="s", tz="utc") - self._last_roll_ts
        return ts_delta >= pd.Timedelta(self._strategy_params['bar_freq'])

    def _update_price_dfs(self, bar_event: BarEvent) -> None:
        bar = bar_event.data

        # get data-frame for a given symbol (or create it if it is not there yet)
        price_df = self._price_dfs.get(bar.instrument.name, pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume']))

        # create index for the new row
        candle_ts = pd.Timestamp(bar.timestamp, unit="s", tz="utc")

        if len(price_df) > 0 and candle_ts > price_df.index[-1]:
            self._price_df_rolled[bar.instrument.name] = True

        # add the new row to the data-frame
        price_df.loc[candle_ts, :] = {
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        }

        # get "price_df_window" minutes back relative to the last row - this is the time window of prices kept in memory
        begin_ts = candle_ts - pd.Timedelta("{}min".format(self._strategy_params['price_df_min_window']))

        # leave only data from the "price_df_min_window" (drop the rest)
        self._price_dfs[bar.instrument.name] = price_df.loc[begin_ts:candle_ts]

    @abstractmethod
    def _calculate_target_position(self, price_dfs: Dict[str, pd.DataFrame]) -> pd.Series:
        pass
