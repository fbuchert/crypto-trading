from execution.base_execution_engine import BaseExecutionEngine


class KrakenExecutionEngine(BaseExecutionEngine):
    def __init__(self, name: str = 'kraken_execution_engine'):
        super().__init__(name)
        raise NotImplementedError('Kraken execution engine is not implemented yet')
