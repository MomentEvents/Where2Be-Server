#!/bin/bash

MAX_RETRIES=5
SLEEP_TIME=5
NUM_RETRIES=0

while true; do
    python3 -m uvicorn app:app --port 8080 --host 0.0.0.0 --reload && break
    NUM_RETRIES=$((NUM_RETRIES+1))
    if [[ $NUM_RETRIES -eq $MAX_RETRIES ]]; then
        echo "Max retries reached. Exiting..."
        exit 1
    else
        echo "Command failed. Retrying in ${SLEEP_TIME} seconds..."
        sleep ${SLEEP_TIME}
    fi
    sleep 10
done