#!/bin/bash

# Call the test_neo4j_health() function
python3 -c "import asyncio; from common.neo4j.moment_neo4j import test_neo4j_health; exit(asyncio.run(test_neo4j_health()))"

# If neo4j_health is good (exit code is 0), start the worker.
if [ $? -eq 0 ]; then
    echo "Starting Where2Be Worker"
    python3 worker/app.py
else
    echo "Neo4j health check failed. Not starting the Worker."
    exit 1
fi