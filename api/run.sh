#!/bin/bash

sleep 10
python3 -m uvicorn app:app --port 8080 --host 0.0.0.0 --reload