from abc import ABC
from typing import Tuple
from enum import Enum


class PositionStatus(Enum):
    none = 0
    long = 1
    short = -1


class StrategyAbstract(ABC):
    def calculate(self, prices, params) -> Tuple[float, float]:
        raise NotImplementedError
