import os
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import BaseModel
from . import models


engine = create_engine(os.environ.get('DB_URI'))
BaseModel.metadata.bind = engine
session = sessionmaker(bind=engine)()


def get_top_reports(datetime_from=None, datetime_to=None, strategy=None, instrument_ticker=None):
    result = session.query(
        models.TestReport.datetime,
        models.TestReport.datetime_from,
        models.TestReport.datetime_to,
        models.TestReport.strategy,
        models.TestReport.hold_profit,
        models.TestReport.strategy_profit,
        models.FinancialInstrument.ticker,
    ).join(
        models.FinancialInstrument,
        models.FinancialInstrument.id == models.TestReport.financial_instrument_id
    )
    if datetime_from:
        result = result.filter(models.TestReport.datetime >= datetime_from)
    if datetime_to:
        result = result.filter(models.TestReport.datetime < datetime_to)
    if strategy:
        result = result.filter(models.TestReport.strategy == strategy)
    if instrument_ticker:
        result = result.filter(models.FinancialInstrument.ticker == instrument_ticker)
    return result.order_by(models.TestReport.strategy_profit.desc()).distinct(
        models.TestReport.datetime_from,
        models.TestReport.datetime_to,
        models.TestReport.strategy_profit,
        models.TestReport.hold_profit,
        models.TestReport.strategy,
        models.TestReport.financial_instrument,
    ).limit(10).all()


def get_report(datetime_from, datetime_to, strategy, financial_instrument_id, interval):
    return session.query(models.TestReport).filter(
        models.TestReport.strategy == strategy,
        models.TestReport.financial_instrument_id == financial_instrument_id,
        models.TestReport.datetime_from <= datetime_from,
        models.TestReport.datetime_to >= datetime_to,
        models.TestReport.interval == interval
    ).first()


def get_instrument(ticker):
    return session.query(models.FinancialInstrument).filter(
        models.FinancialInstrument.ticker == ticker
    ).first()


def get_or_create_instrument(instrument: models.FinancialInstrument):
    instance = session.query(models.FinancialInstrument).filter(
        models.FinancialInstrument.ticker == instrument.ticker
    ).first()
    if instance is not None:
        return instance, False

    session.add(instrument)
    session.commit()
    return instrument, True


def write_report(
    datetime,
    datetime_from,
    datetime_to,
    strategy,
    interval,
    hold_profit,
    strategy_profit,
    financial_instrument_id
):
    session.add(models.TestReport(
        datetime=datetime,
        datetime_from=datetime_from,
        datetime_to=datetime_to,
        strategy=strategy,
        interval=interval,
        hold_profit=hold_profit,
        strategy_profit=strategy_profit,
        financial_instrument_id=financial_instrument_id
    ))
    session.commit()


def get_prices(datetime_from, datetime_to, financial_instrument_id, interval):
    return session.query(models.PriceCandle).filter(
        models.PriceCandle.financial_instrument_id == financial_instrument_id,
        models.PriceCandle.interval == interval,
        models.PriceCandle.datetime >= datetime_from,
        models.PriceCandle.datetime <= datetime_to
    ).distinct(models.PriceCandle.datetime).order_by(models.PriceCandle.datetime).all()


def write_prices(prices, financial_instrument_id, interval):
    session.bulk_save_objects([
        models.PriceCandle(
            financial_instrument_id=financial_instrument_id,
            interval=interval,
            datetime=p['time'],
            price_open=p['o'],
            price_close=p['c'],
            price_max=p['h'],
            price_min=p['l'],
        ) for p in prices
    ])
    session.commit()
