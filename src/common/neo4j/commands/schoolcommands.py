from common.neo4j.moment_neo4j import get_neo4j_session
from common.neo4j.converters import convert_school_entity_to_school, convert_user_entity_to_user
from common.s3.moment_s3 import get_bucket_url
from common.models import Problem
from dateutil import parser
import secrets
import random

def create_school_entity(school_id: str, name: str, abbreviation: str, latitude: float, longitude: float, email_domain: str):
    with get_neo4j_session() as session:

        result = session.run(
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

def get_school_entity_by_school_id(school_id: str):
    with get_neo4j_session() as session:
        result = session.run(
                """
                MATCH(s:School{SchoolID: $school_id})
                RETURN s""",
                parameters={
                    "school_id": school_id,
                },
            )
        record = result.single()
        if record == None:
            return None

        data = record[0]

        school_data = convert_school_entity_to_school(data)

        return school_data
    
def get_school_entity_by_email_domain(email_domain: str):
    with get_neo4j_session() as session:
        result = session.run(
                """
                MATCH(s:School{EmailDomain: $email_domain})
                RETURN s""",
                parameters={
                    "email_domain": email_domain,
                },
            )
        
        record = result.single()

        if record == None:
            return None

        data = record[0]

        school_data = convert_school_entity_to_school(data)

        return school_data
    
def get_all_school_entities():
    with get_neo4j_session() as session:
        # check if email exists
        result = session.run(
            """MATCH (s:School) 
            RETURN s
            ORDER BY toLower(s.Abbreviation + s.Name)""",
        )


        school_array = []
        for record in result:

            if record == None:
                return []
            data = record[0]
            school_array.append(convert_school_entity_to_school(data)
            )
        
        return school_array

def get_all_users_by_school(school_id:str):
    with get_neo4j_session() as session:
        # check if email exists
        result = session.run(
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
            data = record[0]
            user_array.append(convert_user_entity_to_user(data, get_push_token=True))
        
        return user_array
