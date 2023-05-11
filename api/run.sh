#!/bin/bash

echo "Attempting to start Moment server..."

# Call the test_neo4j_health() function and store the result
health_check_result=$(python3 -c "from cloud_resources.moment_neo4j import test_neo4j_health; print(test_neo4j_health())")

# If the function returns True, start the uvicorn server and exit the loop
if [ $health_check_result = "True" ]; then
    echo "Neo4j is healthy, starting the server..."
    ip_address=$(python3 -c "from helpers import get_ip_address; print(get_ip_address())")
    echo "Running Moment server on ${get_ip_address}"
    python3 -m uvicorn app:app --port 8080 --host 0.0.0.0 --reload
    break
fi

# If the function returns False, wait for 5 seconds and increment the retry counter
echo "Neo4j is not healthy, retrying..."
exit 1





