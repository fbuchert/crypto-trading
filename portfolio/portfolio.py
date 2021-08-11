import os
import pickle
import logging
import pandas as pd

from typing import List, Tuple
from core.instrument import Instrument
from core.events import TradeExecutedEvent

rootLogger = logging.getLogger()


class Portfolio:
    def __init__(self, instruments: List[Instrument], save_path: str = ''):
        self._save_path: str = save_path
        self._current_position = self._load_position(instruments)

    @staticmethod
    def _init_position(instruments: List[Instrument]) -> pd.Series:
        return pd.Series({instrument.name: 0.0 for instrument in instruments})

    def _load_position(self, instruments: List[Instrument]) -> pd.Series:
        if self._save_path and os.path.exists(self._save_path):
            rootLogger.info(f'Loading strategy positions from {self._save_path}')
            with open(self._save_path, 'rb') as handle:
                current_position = pd.Series(pickle.load(handle))

            if set(current_position.index) != set(instrument.name for instrument in instruments):
                rootLogger.info(f'Instruments of loaded position series does not match {instruments}.'
                                f'Initializing position series to 0.')
                current_position = Portfolio._init_position(instruments)
        else:
            rootLogger.info(f'{self._save_path} does not exist. Initializing position series to 0.')
            current_position = Portfolio._init_position(instruments)
        return current_position

    def _save_current_position(self) -> None:
        with open(self._save_path, 'wb') as handle:
            pickle.dump(self._current_position.to_dict(), handle, protocol=pickle.HIGHEST_PROTOCOL)

    def get_current_position(self) -> pd.Series:
        return self._current_position

    def handle_execution(self, event: TradeExecutedEvent):
        order = event.data
        self._current_position.loc[order.instrument.name] += order.size
        if self._save_path:
            self._save_current_position()
