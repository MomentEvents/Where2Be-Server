FROM python:3.9

# set directory for requirements
WORKDIR /Moment-Server

RUN apt-get update && apt-get install -y libgl1-mesa-glx

COPY requirements.txt .

COPY ./.env.api .
COPY ./.env.database .

# install dependencies
RUN pip3 install -r requirements.txt

# set directory for api
WORKDIR /Moment-Server/api

COPY ./api .

# RUN python3 ./database_resources/neo4j_database.py

# # make script executable
# RUN chmod +x /Moment-Server/run.sh

# port number it should expose
EXPOSE 8080

CMD ["sh","./run.sh"]