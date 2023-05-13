FROM python:3.9

# set directory for requirements
WORKDIR /

RUN apt-get update && apt-get install -y libgl1-mesa-glx

COPY api_requirements.txt .
COPY common common
COPY api api

RUN pip3 install -r api_requirements.txt

EXPOSE 8080

CMD ["sh", "./api/run.sh"]