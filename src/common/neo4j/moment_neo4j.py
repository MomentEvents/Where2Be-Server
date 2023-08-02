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

    @staticmethod
    async def get_driver_instance():
        attempts = 1
        max_attempts = 5
        while attempts < max_attempts:
            try:
                if Neo4jDriverSingleton._driver_instance is None:
                    Neo4jDriverSingleton.create_driver_instance()
                driver = Neo4jDriverSingleton._driver_instance
                await driver.verify_connectivity()
                return driver
            except:
                print("Unable to connect to the Neo4j database. Retrying attempt #", str(attempts))
                await Neo4jDriverSingleton.close_driver_instance()
            attempts = attempts + 1
        raise Exception("Unable to create a Neo4j session after ", str(max_attempts), " attempts.")

    @staticmethod
    def create_driver_instance():
        if Neo4jDriverSingleton._driver_instance is not None:
            return

        # Create a driver for the Neo4j database
        Neo4jDriverSingleton._driver_instance = AsyncGraphDatabase.driver(
            NEO4J_BOLT_URL, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    @staticmethod
    async def close_driver_instance():
        if Neo4jDriverSingleton._driver_instance is not None:
            await Neo4jDriverSingleton._driver_instance.close()
            Neo4jDriverSingleton._driver_instance = None
            

async def run_neo4j_query(query: str, parameters=None):
    driver = await Neo4jDriverSingleton.get_driver_instance()
    session = driver.session()
    try:
        result = await session.run(query, parameters)
        data = await result.data()
        # print()
        # print("QUERY RESULT IS ", data, "\n\n")
        return data
    except asyncio.CancelledError:
        session.cancel()
        raise
    finally:
        await session.close()

async def test_neo4j_health():
    try:
        driver = await Neo4jDriverSingleton.get_driver_instance()
        await driver.verify_connectivity()
        return 0

    except Exception as e:
        return str(e)


def parse_neo4j_data(data, mode: "str"):
    if(mode == 'single'):
        if(not data):
            return None
    
        parsed_data = list(data[0].values())[0]

        print(parsed_data)

        return parsed_data
    
    elif (mode == 'multiple'):
        if(not data):
            return None
        parsed_data = data[0]
        return parsed_data
    
    raise ValueError('parse_neo4j_data error: cannot accept mode: ', mode)