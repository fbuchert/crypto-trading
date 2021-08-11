import pandas as pd
from typing import Dict
from strategy.bar_strategy_base import BarStrategyBase


class ExampleBarStrategy(BarStrategyBase):
    def __init__(self, config: Dict, strategy_name: str = 'example_strategy'):
        super().__init__(config, strategy_name)

    def _get_historical_price_data(self) -> None:
        raise NotImplementedError('Loading of historical price data is not supported yet.')

    def _calculate_target_position(self, price_dfs: Dict[str, pd.DataFrame]) -> pd.Series:
        # Naive long-only strategy: Go long if close > open of current bar (independent of bar freq / timeframe)
        target_positions = {}
        for k, v in price_dfs.items():
            target_positions[k] = int(v['close'].iloc[-1] > v['open'].iloc[-1])

        normalizer = sum(target_positions.values())
        if normalizer == 0:
            return pd.Series(target_positions)
        else:
            return pd.Series({k: v / normalizer for k, v in target_positions.items()})