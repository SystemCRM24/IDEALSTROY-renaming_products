FROM python:3.13-alpine


WORKDIR /app


COPY .env /app/
COPY bitrix.py /app/
COPY requirements.txt /app/
COPY main.py /app/

RUN pip install --no-cache-dir --upgrade -r requirements.txt