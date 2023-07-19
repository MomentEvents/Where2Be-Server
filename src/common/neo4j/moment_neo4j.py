import os
from neo4j import GraphDatabase

async def run_neo4j_command(query, parameters=None):
    driver = get_neo4j_driver()
    session = driver.session()
    try:
        result = await run_neo4j_command(
                query,
                parameters=parameters,
            )
        
        driver.close()
        return result
    except Exception as e:
        driver.close()
        raise e



async def test_neo4j_health():
    try:
        await run_neo4j_command("MATCH (n) RETURN n LIMIT 1")
        return True

    except:
        return False

def get_neo4j_driver():
    # Set the connection details for the Neo4j database
    NEO4J_BOLT_URL = os.environ.get('NEO4J_BOLT_URL')
    NEO4J_USERNAME = os.environ.get('NEO4J_USERNAME')
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')

    # Create a driver for the Neo4j database
    driver = GraphDatabase.driver(
        NEO4J_BOLT_URL, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    return driver
