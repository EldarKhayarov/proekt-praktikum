from ._strategy_register import *
from .ama import StrategyAMA

strategies = {
    "AMA": StrategyAMA(),
}
