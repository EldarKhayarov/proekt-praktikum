from typing import Dict, Union, Optional, List
import datetime
import logging

from fastapi import FastAPI, Response, status
from pydantic import BaseModel
from openapi_genclient.exceptions import ApiException

from .. import core
from .exceptions import ValidationError, ObjectNotFound


app = FastAPI()


DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


class GetResultsIn(BaseModel):
    datetime_from: Optional[str]
    datetime_to: Optional[str]
    strategy_code: Optional[str]
    instrument_ticker: Optional[str]


class Price(BaseModel):
    datetime: str
    open: float
    close: float
    high: float
    close: float
    period: str


class GetPrices(BaseModel):
    datetime_from: str
    datetime_to: str
    instrument_ticker: str


class GetPricesIn(GetPrices):
    broker_token: str


class GetPricesOut(GetPrices):
    prices: List[Price]


class ReportResult(GetPrices):
    datetime: str
    strategy_profit: float
    hold_profit: float
    strategy_code: str


class GetResultsOut(GetResultsIn):
    results: List[ReportResult]


class TestStrategyIn(GetPrices):
    broker_token: str
    strategy_code: str
    strategy_params: Dict[str, Union[int, float]]


class TestStrategyOut(GetPrices):
    strategy_code: str
    strategy_params: Dict[str, Union[int, float]]
    strategy_profit: float
    hold_profit: float


class TrainStrategyIn(TestStrategyIn):
    strategy_params: Dict[str, List[Union[int, float]]]


class TrainStrategyOut(TestStrategyOut):
    pass


@app.get("/test_strategy", response_model=TestStrategyOut)
def test_strategy(request_data: TestStrategyIn, response: Response):
    try:
        datetime_from, datetime_to = prepare_and_validate_periods(
            request_data.datetime_from, request_data.datetime_to
        )
    except (ValidationError, ValueError):
        print('Wrong dates formats.')
        response.status_code = status.HTTP_400_BAD_REQUEST
        return
    try:
        result = core.test_strategy(
            datetime_from=datetime_from,
            datetime_to=datetime_to,
            broker_token=request_data.broker_token,
            instrument_ticker=request_data.instrument_ticker,
            strategy_code=request_data.strategy_code,
            strategy_params=request_data.strategy_params
        )
        request_dict = request_data.dict()
        return TestStrategyOut(**request_dict, **result)
    except (ApiException, ObjectNotFound) as e:
        print(e)
        response.status_code = status.HTTP_404_NOT_FOUND
    except ValueError as e:
        print(e)
        response.status_code = status.HTTP_400_BAD_REQUEST


@app.get("/train_strategy", response_model=TrainStrategyOut)
def train_strategy(request_data: TrainStrategyIn, response: Response):
    try:
        datetime_from, datetime_to = prepare_and_validate_periods(
            request_data.datetime_from, request_data.datetime_to
        )
    except (ValidationError, ValueError):
        print('Wrong dates formats.')
        response.status_code = status.HTTP_400_BAD_REQUEST
        return
    try:
        result = core.train_strategy(
            datetime_from=datetime_from,
            datetime_to=datetime_to,
            broker_token=request_data.broker_token,
            instrument_ticker=request_data.instrument_ticker,
            strategy_code=request_data.strategy_code,
            strategy_params=request_data.strategy_params
        )
        request_dict = request_data.dict()
        request_dict.update(result)
        return TestStrategyOut(**request_dict)
    except (ApiException, ObjectNotFound) as e:
        print(e)
        response.status_code = status.HTTP_404_NOT_FOUND
    except (ValueError, KeyError) as e:
        print(e)
        response.status_code = status.HTTP_400_BAD_REQUEST


@app.get("/get_results", response_model=GetResultsOut)
def get_results(request_data: GetResultsIn, response: Response):
    try:
        datetime_from = datetime.datetime.strptime(
            request_data.datetime_from, DATETIME_FORMAT) if request_data.datetime_from else None
        datetime_to = datetime.datetime.strptime(
            request_data.datetime_from, DATETIME_FORMAT) if request_data.datetime_to else None
    except ValueError:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return

    if request_data.datetime_from and request_data.datetime_to:
        try:
            datetime_from, datetime_to = prepare_and_validate_periods(
                request_data.datetime_from, request_data.datetime_to
            )
        except ValidationError:
            logging.info('Wrong dates formats.')
            response.status_code = status.HTTP_400_BAD_REQUEST
            return

    try:
        reports = core.get_top_results(
            datetime_from,
            datetime_to,
            request_data.strategy_code,
            request_data.instrument_ticker
        )
    except ObjectNotFound:
        response.status_code = status.HTTP_404_NOT_FOUND
        return

    result = GetResultsOut(
        datetime_from=datetime_from.strftime(DATETIME_FORMAT) if request_data.datetime_from else None,
        datetime_to=datetime_to.strftime(DATETIME_FORMAT) if request_data.datetime_to else None,
        strategy_code=request_data.strategy_code,
        results=list([ReportResult(
            datetime=report['datetime'].strftime(DATETIME_FORMAT),
            datetime_from=report['datetime_from'].strftime(DATETIME_FORMAT),
            datetime_to=report['datetime_to'].strftime(DATETIME_FORMAT),
            strategy_code=report['strategy'],
            hold_profit=report['hold_profit'],
            strategy_profit=report['strategy_profit'],
            instrument_ticker=report['instrument_ticker']
        ) for report in reports])
    )
    return result


@app.get("/prices", response_model=GetPricesOut)
def get_prices(request_data: GetPricesIn, response: Response):
    if request_data.datetime_from and request_data.datetime_to:
        try:
            datetime_from, datetime_to = prepare_and_validate_periods(
                request_data.datetime_from, request_data.datetime_to
            )
        except ValidationError:
            print('Wrong dates formats.')
            response.status_code = status.HTTP_400_BAD_REQUEST
            return
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return
    try:
        result = core.get_prices(
            datetime_from=datetime_from,
            datetime_to=datetime_to,
            broker_token=request_data.broker_token,
            instrument_ticker=request_data.instrument_ticker,
        )
        return GetPricesOut(**result)
    except (ApiException, ObjectNotFound) as e:
        print(e)
        response.status_code = status.HTTP_404_NOT_FOUND


def prepare_and_validate_periods(datetime_from: str, datetime_to: str):
    if not isinstance(datetime_from, datetime.datetime):
        datetime_from = datetime.datetime.strptime(datetime_from, DATETIME_FORMAT)
    if not isinstance(datetime_to, datetime.datetime):
        datetime_to = datetime.datetime.strptime(datetime_to, DATETIME_FORMAT)

    if datetime_from >= datetime_to:
        raise ValidationError
    return datetime_from, datetime_to

