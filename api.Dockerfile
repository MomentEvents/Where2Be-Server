FROM python:3.9
WORKDIR /
RUN apt-get update && apt-get install -y libgl1-mesa-glx
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY api api
COPY common common
EXPOSE 8080
CMD uvicorn api.app:app --reload --host 0.0.0.0 --port 8080