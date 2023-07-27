import os
from neo4j import GraphDatabase


#temp
from dotenv import load_dotenv
# Load .env file
load_dotenv("../.env")


def test_neo4j_health():
    try:
        with get_neo4j_session() as session:
            session.run("MATCH (n) RETURN n LIMIT 1")
        return 0

    except Exception as e:
        return str(e)

def get_neo4j_session():
    driver = get_neo4j_driver()
    driver_session = driver.session()
    return driver_session


def get_neo4j_driver():
    # Set the connection details for the Neo4j database
    NEO4J_BOLT_URL = os.environ.get('NEO4J_BOLT_URL')
    NEO4J_USERNAME = os.environ.get('NEO4J_USERNAME')
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')

    print("NEO4J_BOLT_URL",NEO4J_BOLT_URL)

    # Create a driver for the Neo4j database
    driver = GraphDatabase.driver(
        NEO4J_BOLT_URL, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    return driver
