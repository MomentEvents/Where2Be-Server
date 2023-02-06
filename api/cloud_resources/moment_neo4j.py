from neo4j import GraphDatabase

def get_connection():
    driver = get_neo4j_driver()
    driver_session = driver.session()
    return driver_session

def get_neo4j_driver():
    # Set the connection details for the Neo4j database
    NEO4J_URI = "neo4j+s://32c386b6.databases.neo4j.io"
    NEO4J_USERNAME = "neo4j"
    NEO4J_PASSWORD = "lXx1rWQyLKFNkRk3YbZrs0fNf8s5ujqBmA3HC5edcFk"

    # Create a driver for the Neo4j database
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    return driver