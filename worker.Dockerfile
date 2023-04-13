# syntax=docker/dockerfile:1
FROM python:3.10.8-slim-buster
WORKDIR /
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
WORKDIR /worker
COPY ./worker .
CMD python -m app