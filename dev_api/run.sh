#!/bin/bash

python3 -m uvicorn app:app --port 8070 --host 0.0.0.0 --reload
