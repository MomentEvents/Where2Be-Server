# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the docker image
WORKDIR /app

RUN apt-get update && apt-get install -y libgl1-mesa-glx

# Create a directory for the transformers cache
RUN mkdir -p /app/scraper/cache

# Copy the scripts to the scraper directory
COPY ./api_connect.py /app/scraper/
COPY ./ /app/scraper/
COPY ./events_from_discord.py /app/scraper/

# Update pip
RUN pip install --upgrade pip

# If you have requirements.txt or other dependencies, make sure to copy and install them:
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Change the working directory to scraper before running the script
WORKDIR /app/scraper

# Command to run your script
CMD ["python", "./events_from_discord.py"]
