# syntax=docker/dockerfile:1
FROM python:3.9

# set directory for requirements
WORKDIR /

RUN apt-get update && apt-get install -y libgl1-mesa-glx

WORKDIR /worker
COPY ./worker .
CMD python3 app.py