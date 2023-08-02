from common.neo4j.moment_neo4j import get_neo4j_session, parse_neo4j_data, run_neo4j_query
from common.neo4j.converters import convert_school_entity_to_school, convert_user_entity_to_user
from common.s3.moment_s3 import get_bucket_url
from common.models import Problem
from dateutil import parser
import secrets
import random

async def create_school_entity(school_id: str, name: str, abbreviation: str, latitude: float, longitude: float, email_domain: str):

    result = await run_neo4j_query(
        """CREATE (s:School {SchoolID: $school_id, Name: $name, Abbreviation: $abbreviation, Latitude: $latitude, Longitude: $longitude, EmailDomain: $email_domain})
        RETURN s""",
        parameters={
            "school_id": school_id,
            "name": name,
            "abbreviation": abbreviation,
            "latitude": latitude,
            "longitude": longitude,
            "email_domain": email_domain
        },
    )

    return school_id

async def get_school_entity_by_school_id(school_id: str):

    result = await run_neo4j_query(
            """
            MATCH(s:School{SchoolID: $school_id})
            RETURN s""",
            parameters={
                "school_id": school_id,
            },
        )
    
    data = parse_neo4j_data(result, 'single')

    if(not data):
        return None

    school_data = convert_school_entity_to_school(data)

    return school_data

async def get_school_entity_by_user_id(user_id: str):
    result = await run_neo4j_query(
        """
            MATCH (u:User{UserID : $user_id})-[:user_school]->(s:School) return s""",
        parameters={
            "user_id": user_id,
        },
    )
    
    data = parse_neo4j_data(result, 'single')

    if(not data):
        return None

    school_data = convert_school_entity_to_school(data)

    return school_data 
    
async def get_school_entity_by_email_domain(email_domain: str):
        
        result = await run_neo4j_query(
                """
                MATCH(s:School{EmailDomain: $email_domain})
                RETURN s""",
                parameters={
                    "email_domain": email_domain,
                },
            )
        
        data = parse_neo4j_data(result, 'single')

        if(not data):
            return None

        school_data = convert_school_entity_to_school(data)

        return school_data
    
async def get_all_school_entities():
    # check if email exists
    result = await run_neo4j_query(
        """MATCH (s:School) 
        RETURN s
        ORDER BY toLower(s.Abbreviation + s.Name)""",
    )


    school_array = []
    for record in result:

        if record == None:
            return []
        data = record['s']
        school_array.append(convert_school_entity_to_school(data)
        )

    return school_array

async def get_all_users_by_school(school_id:str, get_push_token=False):
    
    result = await run_neo4j_query(
        """MATCH (s:School {SchoolID: $school_id})<-[:user_school]-(u:User)
        RETURN u""",
        parameters={
            "school_id": school_id
        }
    )
    
    user_array = []
    for record in result:

        if record == None:
            return []
        data = record['u']
        user_array.append(convert_user_entity_to_user(data, get_push_token))
    
    return user_array
