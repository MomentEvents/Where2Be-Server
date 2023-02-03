#!/bin/bash

python3 -m uvicorn api.app:app --port 8080 --host 0.0.0.0 --reload
