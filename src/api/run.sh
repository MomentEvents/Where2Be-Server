#!/bin/bash

# NOTE: Make sure to call ./api/run.sh outside the directory!

echo "Attempting to start Moment server..."

# Call the test_neo4j_health() function and store the result
neo4j_health=$(python3 -c "from common.neo4j.moment_neo4j import test_neo4j_health; print(test_neo4j_health())")

# If the function returns True, start the uvicorn server and exit the loop
if [ $neo4j_health = "True" ]; then
    echo "Neo4j is healthy, starting the server..."
    python3 -m uvicorn api.app:app --port 8080 --host 0.0.0.0 --reload
    break
fi

# If the function returns False, wait for 5 seconds and increment the retry counter
echo "Neo4j is not healthy, retrying..."
exit 1





