FROM python:3.9

# set directory for requirements
WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y libgl1-mesa-glx

COPY common common
COPY worker worker

RUN pip3 install -r worker/requirements.txt
RUN pip3 install -r common/requirements.txt

CMD ["sh", "./worker/run.sh"]