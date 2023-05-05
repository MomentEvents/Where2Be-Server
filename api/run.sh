#!/bin/bash

# Run the Python script to test Neo4j health, and retry up to 10 times
retry_count=1
while [ $retry_count -lt 10 ]; do

    echo "Attempting to start Moment server. Try #$retry_count"

    # Call the test_neo4j_health() function and store the result
    health_check_result=$(python3 -c "from cloud_resources.moment_neo4j import test_neo4j_health; print(test_neo4j_health())")

    # If the function returns True, start the uvicorn server and exit the loop
    if [ $health_check_result = "True" ]; then
        echo "Neo4j is healthy, starting the server..."
        python3 -m uvicorn app:app --port 8080 --host 0.0.0.0 --reload
        break
    fi

    # If the function returns False, wait for 5 seconds and increment the retry counter
    echo "Neo4j is not healthy, retrying..."
    exit 1
done

# # If the script has retried 10 times and still failed, exit with return code -1
# if [ $retry_count -eq 10 ]; then
#     echo "Neo4j is still not healthy after 10 retries. Exiting..."
#     exit -1
# fi





