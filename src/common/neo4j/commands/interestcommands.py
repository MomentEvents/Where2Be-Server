from common.neo4j.moment_neo4j import get_neo4j_session, run_neo4j_query
from common.s3.moment_s3 import get_bucket_url
from common.models import Problem
from dateutil import parser
import secrets
import random

async def create_interest_entity(interest_id: str, name: str):

    result = await run_neo4j_query(
        """CREATE (i:Interest {InterestID: $interest_id, Name: $name})
        RETURN i""",
        parameters={
            "interest_id": interest_id,
            "name": name,
        },
    )

    return interest_id
