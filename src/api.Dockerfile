FROM python:3.9

# set directory for requirements
WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y libgl1-mesa-glx

COPY common common
COPY api api

RUN pip3 install -r api/requirements.txt
RUN pip3 install -r common/requirements.txt

EXPOSE 8080

CMD ["sh", "./api/run.sh"]