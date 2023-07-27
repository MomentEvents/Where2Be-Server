import os
from neo4j import GraphDatabase

class Neo4jDriverSingleton:
    _driver_instance = None

    @staticmethod
    def get_driver_instance():
        if Neo4jDriverSingleton._driver_instance is None:
            Neo4jDriverSingleton.create_driver_instance()

        return Neo4jDriverSingleton._driver_instance

    @staticmethod
    def create_driver_instance():
        if(Neo4jDriverSingleton._driver_instance is not None):
            Neo4jDriverSingleton._driver_instance.close()
        # Set the connection details for the Neo4j database
        NEO4J_BOLT_URL = os.environ.get('NEO4J_BOLT_URL')
        NEO4J_USERNAME = os.environ.get('NEO4J_USERNAME')
        NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')

        # Create a driver for the Neo4j database
        Neo4jDriverSingleton._driver_instance = GraphDatabase.driver(
            NEO4J_BOLT_URL, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        
    @staticmethod
    def close_driver_instance():
        if(Neo4jDriverSingleton._driver_instance is not None):
            Neo4jDriverSingleton._driver_instance.close()

def get_neo4j_session():
    try:
        driver = Neo4jDriverSingleton.get_driver_instance()
        driver.verify_connectivity()
        driver_session = driver.session()
        print("RETURNING SESSION")
        return driver_session
    except:
        Neo4jDriverSingleton.close_driver_instance()
        print("attempting to get neo4j driver again...")
        Neo4jDriverSingleton.create_driver_instance()
        driver = Neo4jDriverSingleton.get_driver_instance()
        driver.verify_connectivity()
        driver_session = driver.session()
        print("successfully created a new neo4j driver!")
        return driver_session

def test_neo4j_health():
    try:
        driver = Neo4jDriverSingleton.get_driver_instance()
        driver.verify_connectivity()
        Neo4jDriverSingleton.close_driver_instance()
        return 0

    except Exception as e:
        return str(e)