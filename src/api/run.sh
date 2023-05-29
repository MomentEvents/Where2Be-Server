#!/bin/bash

# NOTE: Make sure to call ./api/run.sh outside the directory!

# Call the test_neo4j_health() function and store the result
neo4j_health=$(python3 -c "from common.neo4j.moment_neo4j import test_neo4j_health; print(test_neo4j_health())")
# sql_health=$(python3 -c "from common.sql.moment_sql import test_sql_health; print(test_sql_health())")

# If neo4j_health is good, start the api.
if [ "$neo4j_health" = "True" ]; then
    echo "Starting Moment API"
    python3 -m uvicorn api.app:app --port 8080 --host 0.0.0.0 --reload
    exit 0
fi

exit 1





