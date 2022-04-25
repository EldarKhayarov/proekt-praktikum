import pytz
from datetime import datetime
from typing import Optional

from openapi_client import openapi

from . import BrokerClientAbstract


class TinkoffBrokerClient(BrokerClientAbstract):
    def __init__(self, token):
        self.token = token
        self.client = openapi.sandbox_api_client(self.token)

    def get_instrument_by_ticker(self, ticker: str) -> Optional[dict]:
        response = self.client.market.market_search_by_ticker_get(ticker).to_dict()
        instruments = response['payload']['instruments']
        if len(instruments) > 0:
            return instruments[0]
        return None

    def get_prices(
            self, ticker: str, datetime_from: datetime,
            datetime_to: datetime, interval: str,
            figi: Optional[str] = None
    ) -> dict:
        if not figi:
            figi = self.get_instrument_by_ticker(ticker)['figi']
        if datetime_from.year == datetime_to.year:
            prices = self.client.market.market_candles_get(
                figi=figi,
                _from=datetime_from,
                to=datetime_to,
                interval=interval
            ).to_dict()['payload']['candles']
        else:
            prices = []
            for year in range(datetime_from.year, datetime_to.year + 1):
                to = datetime(year, 12, 31, 23, 59, 59, tzinfo=pytz.UTC)
                from_ = datetime(year, 1, 1, tzinfo=pytz.UTC)
                if year == datetime_from.year:
                    from_ = datetime_from
                elif year == datetime_to.year:
                    to = datetime_to
                prices.extend(self.client.market.market_candles_get(
                    figi=figi,
                    _from=from_,
                    to=to,
                    interval=interval
                ).to_dict()['payload']['candles'])

        return prices
