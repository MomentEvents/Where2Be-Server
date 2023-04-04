FROM python:3.9

# set directory for requirements
WORKDIR /Moment-Server

COPY requirements.txt .

# install dependencies
RUN pip3 install -r requirements.txt

RUN apt-get update && apt-get install -y libgl1-mesa-glx

# set directory for api
WORKDIR /Moment-Server/api

COPY ./api .

# exclude .git directory from the COPY command
# COPY --exclude=.git ./ /Moment-Server/

# port number it should expose
EXPOSE 8080

CMD ["sh", "./run.sh"]