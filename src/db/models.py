from enum import Enum

from sqlalchemy import Column, ForeignKey
from sqlalchemy import types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

BaseModel = declarative_base()


class FinancialInstrumentType(Enum):
    stock = 0
    bond = 1
    futures = 2

    def __str__(self):
        return self.name


class FinancialInstrument(BaseModel):
    __tablename__ = 'financial_instrument'

    id = Column(types.Integer, primary_key=True)
    ticker = Column(types.String(12), nullable=False, unique=True)
    # type = Column(types.Enum(FinancialInstrumentType), nullable=False)
    figi = Column(types.String(12), nullable=False, unique=True)
    name = Column(types.String(255), nullable=False, unique=True)


class PriceCandle(BaseModel):
    __tablename__ = 'price_candle'

    id = Column(types.Integer, primary_key=True)
    datetime = Column(types.DateTime, nullable=False)
    interval = Column(types.String(5), nullable=False, default='1min')
    price_open = Column(types.Float, nullable=False)
    price_close = Column(types.Float, nullable=False)
    price_max = Column(types.Float, nullable=False)
    price_min = Column(types.Float, nullable=False)
    financial_instrument_id = Column(
        types.Integer,
        ForeignKey('financial_instrument.id', ondelete='CASCADE'),
        nullable=False
    )

    financial_instrument = relationship(
        'FinancialInstrument',
        cascade='all, delete',
        backref='price_candles'
    )


class TestReport(BaseModel):
    __tablename__ = 'test_report'

    id = Column(types.Integer, primary_key=True)
    datetime = Column(types.DateTime, nullable=False)
    datetime_from = Column(types.DateTime, nullable=False)
    datetime_to = Column(types.DateTime, nullable=False)
    strategy = Column(types.String(16), nullable=False)
    interval = Column(types.String(5), nullable=False, default='1min')
    hold_profit = Column(types.Float, nullable=False)
    strategy_profit = Column(types.Float, nullable=False)
    financial_instrument_id = Column(
        types.Integer,
        ForeignKey('financial_instrument.id', ondelete='CASCADE'),
        nullable=False
    )

    financial_instrument = relationship(
        'FinancialInstrument',
        cascade='all, delete',
        backref='test_reports'
    )
