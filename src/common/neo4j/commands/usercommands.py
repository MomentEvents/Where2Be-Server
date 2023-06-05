from common.neo4j.moment_neo4j import get_neo4j_session
from common.neo4j.converters import convert_user_entity_to_user, convert_school_entity_to_school
from common.s3.moment_s3 import get_bucket_url
from common.models import Problem
from dateutil import parser
import secrets
import random


def create_user_entity(display_name: str, username: str, school_id: str, is_verified_org: bool):
    username = username.lower()
    username = username.strip()
    display_name = display_name.strip()

    random_number = str(random.randint(1, 5))
    default_user_image = (
        get_bucket_url()+"app-uploads/images/users/static/default" + random_number + ".png"
    )

    with get_neo4j_session() as session:

        user_access_token = secrets.token_urlsafe()
        user_id = secrets.token_urlsafe()

        result = session.run(
            """CREATE (u:User {UserID: $user_id, Username: $username, Picture:$picture, DisplayName:$display_name, UserAccessToken:$user_access_token, VerifiedOrganization:$is_verified_org})
            WITH u
            MATCH(n:School{SchoolID: $school_id})
            CREATE (u)-[r:user_school]->(n)
            RETURN u""",
            parameters={
                "username": username,
                "display_name": display_name,
                "picture": default_user_image,
                "school_id": school_id,
                "user_access_token": user_access_token,
                "user_id": user_id,
                "is_verified_org": is_verified_org,
            },
        )

        return user_access_token, user_id
 
def get_user_entity_by_username(username: str, self_user_access_token: str, ):


    with get_neo4j_session() as session:

        result = session.run(
            """MATCH (u:User {Username: $username})
            RETURN u""",
            parameters={
                "username": username
            },
        )

        record = result.single()

        if record == None:
            return None

        data = record[0]

        user_data = convert_user_entity_to_user(data)

        return user_data

def get_user_entity_by_user_id(user_id: str):
    with get_neo4j_session() as session:

        result = session.run(
            """MATCH (u:User {UserID: $user_id})
            RETURN u""",
            parameters={
                "user_id": user_id
            },
        )

        record = result.single()

        if record == None:
            return None

        data = record[0]

        user_data = convert_user_entity_to_user(data)

        return user_data
