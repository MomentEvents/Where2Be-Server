#!/bin/bash

# Call the test_neo4j_health() function
python3 -c "from common.neo4j.moment_neo4j import test_neo4j_health; exit(test_neo4j_health())"

# If neo4j_health is good (exit code is 0), start the api.
if [ $? -eq 0 ]; then
    echo "Starting Where2Be API"
    python3 -m uvicorn api.app:app --port 8080 --host 0.0.0.0 --reload
else
    echo "Neo4j health check failed. Not starting the API."
    exit 1
fi