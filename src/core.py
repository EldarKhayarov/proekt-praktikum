from datetime import datetime
from typing import List

from .brokers.tinkoff_adapter import TinkoffBrokerClient
from .strategy_register import strategies
from .api.exceptions import ObjectNotFound, ValidationError
from .db import db


DEFAULT_PRICE_INTERVAL = 'day'

clients = dict()


def get_or_create_client(token: str):
    if token in clients.keys():
        return clients[token]
    clients[token] = TinkoffBrokerClient(token)
    return clients[token]


def fetch_instrument(ticker, broker_token):
    broker_client = get_or_create_client(broker_token)
    instrument = db.get_instrument(ticker=ticker)

    if instrument is None:
        instrument = broker_client.get_instrument_by_ticker(ticker=ticker)
        if instrument is None:
            raise ObjectNotFound
        instrument = db.models.FinancialInstrument(
            ticker=instrument['ticker'],
            figi=instrument['figi'],
            name=instrument['name']
        )

    instrument, created = db.get_or_create_instrument(instrument)
    return instrument


def fetch_prices(
        datetime_from,
        datetime_to,
        broker_token,
        instrument,
        interval,
        strategy
):
    broker_client = get_or_create_client(broker_token)
    report = db.get_report(
        datetime_from=datetime_from,
        datetime_to=datetime_to,
        strategy=strategy,
        financial_instrument_id=instrument.id,
        interval=interval
    )

    if report is None:
        prices = broker_client.get_prices(
            ticker=instrument.ticker,
            datetime_from=datetime_from,
            datetime_to=datetime_to,
            interval=interval,
            figi=instrument.figi
        )
        db.write_prices(prices, interval=interval, financial_instrument_id=instrument.id)
    return db.get_prices(
        datetime_from=datetime_from,
        datetime_to=datetime_to,
        financial_instrument_id=instrument.id,
        interval=interval
    )


def test_strategy(
        datetime_from,
        datetime_to,
        broker_token,
        instrument_ticker,
        strategy_code,
        strategy_params
):
    now = datetime.now()

    interval = DEFAULT_PRICE_INTERVAL

    instrument = fetch_instrument(instrument_ticker, broker_token)

    prices = fetch_prices(datetime_from, datetime_to, broker_token, instrument, interval, strategy_code)

    if not strategies.get(strategy_code):
        raise ObjectNotFound('Strategy not found.')

    try:
        strategy_profit, hold_profit = strategies[strategy_code].calculate(
            [price.price_open for price in prices],
            strategy_params
        )
    except (KeyError, ValueError):
        raise ValidationError('Wrong strategy parameters.')

    if strategy_profit is None or hold_profit is None:
        raise ValidationError('Max strategy param value greater than period.')
    db.write_report(
        datetime=now,
        datetime_from=datetime_from,
        datetime_to=datetime_to,
        strategy=strategy_code,
        interval=interval,
        hold_profit=hold_profit,
        strategy_profit=strategy_profit,
        financial_instrument_id=instrument.id
    )
    return {
        'strategy_profit': strategy_profit,
        'hold_profit': hold_profit
    }


def train_strategy(
        datetime_from,
        datetime_to,
        broker_token,
        instrument_ticker,
        strategy_code,
        strategy_params
) -> dict:

    now = datetime.now()

    interval = DEFAULT_PRICE_INTERVAL

    instrument = fetch_instrument(instrument_ticker, broker_token)

    prices = fetch_prices(datetime_from, datetime_to, broker_token, instrument, interval, strategy_code)

    for dia in strategy_params.values():
        if not (isinstance(dia, list) or isinstance(dia, tuple)):
            raise KeyError("Wrong param type.")
        if not (isinstance(dia[0], int) and isinstance(dia[1], int)):
            raise KeyError("Param must contain integers.")

    if not strategies.get(strategy_code):
        raise ObjectNotFound('Strategy not found.')

    prepared_prices = [price.price_open for price in prices]
    max_profit = -99999.
    max_params = None
    hold_profit = None

    i = 1
    for slow in range(strategy_params['slow'][0], strategy_params['slow'][1] + 1):
        for n in range(strategy_params['n'][0], strategy_params['n'][1] + 1):
            for fast in range(strategy_params['fast'][0], strategy_params['fast'][1] + 1):
                if not slow > n > fast:
                    continue
                params = {
                    'fast': fast,
                    'n': n,
                    'slow': slow
                }
                strategy_profit, hold_profit = strategies[strategy_code].calculate(
                    prepared_prices,
                    params
                )
                if strategy_profit > max_profit:
                    max_profit = strategy_profit
                    max_params = params
                i += 1

    _ = strategies[strategy_code].calculate(prepared_prices, max_params, show_plot=True)

    if hold_profit:
        db.write_report(
            datetime=now,
            datetime_from=datetime_from,
            datetime_to=datetime_to,
            strategy=strategy_code,
            interval=interval,
            hold_profit=hold_profit,
            strategy_profit=max_profit,
            financial_instrument_id=instrument.id
        )

    return {
        'strategy_profit': max_profit,
        'hold_profit': hold_profit,
        'strategy_params': max_params
    }


def get_top_results(from_: datetime, to_: datetime, strategy: str, instrument_ticker: str) -> List[dict]:
    reports = db.get_top_reports(from_, to_, strategy, instrument_ticker)
    return [{
        'datetime': r[0],
        'datetime_from': r[1],
        'datetime_to': r[2],
        'strategy': r[3],
        'hold_profit': r[4],
        'strategy_profit': r[5],
        'instrument_ticker': r[6]
    } for r in reports]


def get_prices(
        datetime_from: datetime,
        datetime_to: datetime,
        broker_token: str,
        instrument_ticker: str,
) -> dict:
    instrument = fetch_instrument(instrument_ticker, broker_token)
    prices = fetch_prices(datetime_from, datetime_to, broker_token, instrument, DEFAULT_PRICE_INTERVAL, None)
    return {
        'datetime_from': str(datetime_from),
        'datetime_to': str(datetime_to),
        'instrument_ticker': instrument_ticker,
        'prices': [
            {
                'datetime': str(price.datetime),
                'open': price.price_open,
                'close': price.price_close,
                'high': price.price_max,
                'low': price.price_min,
                'period': price.interval,
            }
            for price in prices
        ]
    }
