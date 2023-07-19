from common.neo4j.moment_neo4j import get_neo4j_driver, run_neo4j_command
from common.neo4j.converters import convert_school_entity_to_school
from common.s3.moment_s3 import get_bucket_url
from common.models import Problem
from dateutil import parser
import secrets
import random

def create_school_entity(school_id: str, name: str, abbreviation: str, latitude: float, longitude: float):

    result = run_neo4j_command(
        """CREATE (s:School {SchoolID: $school_id, Name: $name, Abbreviation: $abbreviation, Latitude: $latitude, Longitude: $longitude})
        RETURN s""",
        parameters={
            "school_id": school_id,
            "name": name,
            "abbreviation": abbreviation,
            "latitude": latitude,
            "longitude": longitude,
        },
    )

    return school_id

def get_school_entity_by_school_id(school_id: str):
    result = run_neo4j_command(
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
