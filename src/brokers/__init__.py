from datetime import datetime
from abc import ABC
from typing import Optional


class BrokerClientAbstract(ABC):
    def get_instrument_by_ticker(self, ticker: str) -> Optional[dict]:
        raise NotImplementedError

    def get_prices(
            self, ticker: str, date_from: datetime,
            date_to: datetime, interval: str,
            figi: Optional[str]
    ) -> dict:
        raise NotImplementedError
