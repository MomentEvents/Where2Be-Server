from common.neo4j.converters import convert_event_entity_to_event
from common.neo4j.moment_neo4j import parse_neo4j_data, run_neo4j_query
from common.s3.moment_s3 import get_bucket_url
from common.models import Problem
from dateutil import parser
import secrets
import random
from datetime import datetime


async def create_moment_entity(event_id: str, moment_id: str, user_access_token: str, moment_image: str, type: str):

    if (event_id is None):
        return ValueError
    if (moment_id is None):
        moment_id = secrets.token_urlsafe()

    cypher_query = """
        MATCH (user:User {UserAccessToken: $user_access_token}), (event:Event {EventID: $event_id}) 
        CREATE (moment:Moment {
            MomentID: $moment_id,
            Picture: $moment_image,
            Type: $type,
            TimeCreated: datetime()
        })<-[rel:moment_user]-(user),
        (moment)-[:moment_event]->(event)
        """

    result = await run_neo4j_query(
        cypher_query,
        parameters={
            "event_id": event_id,
            "user_access_token": user_access_token,
            "moment_id": moment_id,
            "moment_image": moment_image,
            "type": type,
        },
    )

    return moment_id

async def update_viewed_moments(moment_id: str, user_access_token: str):

    query = """
    MATCH (u1:User{UserID: $from_user_id}),(u2:User{UserID: $to_user_id}) 
    MERGE (u1)-[r:user_follow]->(u2)
    SET r.Timestamp = datetime($timestamp)
    """

    parameters = {
        "from_user_id": from_user_id,
        "to_user_id": to_user_id,
        # Convert DateTime object to ISO 8601 string format
        "timestamp": timestamp.isoformat()
    }

    await run_neo4j_query(query, parameters)

    return 0