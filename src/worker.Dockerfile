FROM python:3.9

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /usr/src/app:$PYTHONPATH

RUN apt-get update && apt-get install -y libgl1-mesa-glx

# copy project
COPY common common
COPY worker worker

# install dependencies
RUN pip install --no-cache-dir -r worker/requirements.txt
RUN pip install --no-cache-dir -r common/requirements.txt

CMD ["sh", "./worker/run.sh"]
