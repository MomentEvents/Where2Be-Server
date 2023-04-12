# syntax=docker/dockerfile:1
FROM python:3.9
WORKDIR /
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY worker worker
COPY common common
CMD python -m worker.app