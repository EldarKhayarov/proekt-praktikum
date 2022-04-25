FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

ENV PYTHONUNBUFFERED 1

RUN apt-get update -y \
  # psycopg2 dependencies
  && apt-get install gcc -y \
  && apt-get install libpq-dev -y


COPY ./requirements.txt /requirements.txt
RUN pip install -i https://test.pypi.org/simple/ --extra-index-url=https://pypi.org/simple/ tinkoff-invest-openapi-client \
  && pip install -r /requirements.txt

COPY ./compose/app/start /start
RUN sed -i 's/\r//' /start
RUN chmod +x /start

WORKDIR /app
