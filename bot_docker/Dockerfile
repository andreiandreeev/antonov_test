FROM python:3.8-slim-buster


WORKDIR /app

RUN pip3 install poetry

COPY trading_robot/ /app/

COPY orders.sql /app/

RUN apt-get update && apt-get install -y git

RUN poetry config virtualenvs.create false \
  && poetry install


CMD ["poetry", "run", "python3", "trading_robot/start.py"]



