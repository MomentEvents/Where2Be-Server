# Start with Python 3.9 base image
FROM python:3.9

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory in container
WORKDIR /usr/src/app

# Install dependencies
RUN apt-get update && apt-get install -y libgl1-mesa-glx

# Copy source code
COPY common common
COPY api api

# Install python dependencies
RUN pip3 install -r api/requirements.txt
RUN pip3 install -r common/requirements.txt

# Expose port 8080
EXPOSE 8080

# Run command
CMD ["sh", "./api/run.sh"]
