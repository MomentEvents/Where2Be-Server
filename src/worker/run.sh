#!/bin/bash

# NOTE: Make sure to call ./worker/run.sh outside the directory!

neo4j_health=$(python3 -c "from common.neo4j.moment_neo4j import test_neo4j_health; print(test_neo4j_health())")

# If the function returns True, start the uvicorn server and exit the loop
if [ $neo4j_health = "True" ]; then
    echo "Starting Moment worker"
    python3 worker/app.py
    break
fi

exit 1