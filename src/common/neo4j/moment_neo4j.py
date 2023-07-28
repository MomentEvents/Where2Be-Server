import asyncio
import os
import time
import logging
from neo4j import GraphDatabase, AsyncGraphDatabase

# Set the connection details for the Neo4j database
NEO4J_BOLT_URL = os.getenv('NEO4J_BOLT_URL')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

class Neo4jDriverSingleton:
    _driver_instance = None
    _bookmark_manager = None

    @staticmethod
    def get_driver_instance():
        if Neo4jDriverSingleton._driver_instance is None:
            Neo4jDriverSingleton.create_driver_instance()
        return Neo4jDriverSingleton._driver_instance
    
    @staticmethod
    def get_bookmark_manager():
        return Neo4jDriverSingleton._bookmark_manager

    @staticmethod
    def create_driver_instance():
        if Neo4jDriverSingleton._driver_instance is not None:
            return

        # Create a driver for the Neo4j database
        Neo4jDriverSingleton._driver_instance = AsyncGraphDatabase.driver(
            NEO4J_BOLT_URL, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        Neo4jDriverSingleton._bookmark_manager = AsyncGraphDatabase.bookmark_manager()

    @staticmethod
    async def close_driver_instance():
        if Neo4jDriverSingleton._driver_instance is not None:
            await Neo4jDriverSingleton._driver_instance.close()
            Neo4jDriverSingleton._driver_instance = None

        if Neo4jDriverSingleton._bookmark_manager is not None:
            Neo4jDriverSingleton._bookmark_manager = None
            

async def get_neo4j_session():
    attempts = 1
    max_attempts = 5
    while attempts < max_attempts:
        try:
            driver = Neo4jDriverSingleton.get_driver_instance()
            bookmark_manager = Neo4jDriverSingleton.get_bookmark_manager()
            await driver.verify_connectivity()
            return driver.session()
        except:
            logging.error("Unable to connect to the Neo4j database. Retrying attempt #", str(attempts))
            Neo4jDriverSingleton.close_driver_instance()
        attempts = attempts + 1
    raise Exception("Unable to create a Neo4j session after ", str(max_attempts), " attempts.")

async def test_neo4j_health():
    try:
        driver = Neo4jDriverSingleton.get_driver_instance()
        await driver.verify_connectivity()
        await Neo4jDriverSingleton.close_driver_instance()
        return 0

    except Exception as e:
        return str(e)
    
async def run_neo4j_query(query: str, parameters=None):
    async with AsyncGraphDatabase.driver(NEO4J_BOLT_URL, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as driver:
        session = driver.session()
        try:
            result = await session.run(query, parameters)
            return await result.value()
        except asyncio.CancelledError:
            session.cancel()
            raise
        finally:
            await session.close()
