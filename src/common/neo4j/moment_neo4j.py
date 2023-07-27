import os
from neo4j import GraphDatabase

class Neo4jDriverSingleton:
    _driver_instance = None

    @staticmethod
    def get_driver_instance():
        if Neo4jDriverSingleton._driver_instance is None:
            # Set the connection details for the Neo4j database
            NEO4J_BOLT_URL = os.environ.get('NEO4J_BOLT_URL')
            NEO4J_USERNAME = os.environ.get('NEO4J_USERNAME')
            NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')

            # Create a driver for the Neo4j database
            Neo4jDriverSingleton._driver_instance = GraphDatabase.driver(
                NEO4J_BOLT_URL, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

        return Neo4jDriverSingleton._driver_instance

def test_neo4j_health():
    try:
        with get_neo4j_session() as session:
            session.run("MATCH (n) RETURN n LIMIT 1")
        return 0

    except Exception as e:
        return str(e)

def get_neo4j_session():
    driver = Neo4jDriverSingleton.get_driver_instance()
    driver_session = driver.session()
    return driver_session