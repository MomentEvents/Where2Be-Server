from dotenv import load_dotenv
import os
import time
import logging
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
        # Set the connection details for the Neo4j database
        NEO4J_BOLT_URL = os.getenv('NEO4J_BOLT_URL')
        NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
        NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

        # Create a driver for the Neo4j database
        Neo4jDriverSingleton._driver_instance = GraphDatabase.driver(
            NEO4J_BOLT_URL, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    @staticmethod
    def close_driver_instance():
        if Neo4jDriverSingleton._driver_instance is not None:
            Neo4jDriverSingleton._driver_instance.close()
            Neo4jDriverSingleton._driver_instance = None


def get_neo4j_session():
    attempts = 1
    max_attempts = 5
    while attempts < max_attempts:
        try:
            driver = Neo4jDriverSingleton.get_driver_instance()
            driver.verify_connectivity()
            return driver.session()
        except:
            logging.error(
                "Unable to connect to the Neo4j database. Retrying attempt #", str(attempts))
            Neo4jDriverSingleton.close_driver_instance()
        attempts = attempts + 1
    raise Exception("Unable to create a Neo4j session after ",
                    str(max_attempts), " attempts.")


# temp
# Load .env file
load_dotenv("../.env")


def test_neo4j_health():
    try:
        driver = Neo4jDriverSingleton.get_driver_instance()
        driver.verify_connectivity()
        Neo4jDriverSingleton.close_driver_instance()
        return 0

    except Exception as e:
        return str(e)
