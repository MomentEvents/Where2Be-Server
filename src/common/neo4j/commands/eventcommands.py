from common.neo4j.moment_neo4j import get_neo4j_session
from common.s3.moment_s3 import get_bucket_url
from common.models import Problem
from dateutil import parser
import secrets
import random

def create_event_entity(user_access_token: str, event_image: str, title: str, description: str, location: str, visibility: str, interest_ids, start_date_time_string, end_date_time_string):
    start_date_time = parser.parse(start_date_time_string)
    end_date_time = None if end_date_time_string is None else parser.parse(end_date_time_string)


    title = title.strip()
    description = description.strip()
    location = location.strip()
    event_id = secrets.token_urlsafe()



    with get_neo4j_session() as session:
        result = session.run(
            """MATCH (user:User {UserAccessToken: $user_access_token})-[:user_school]->(school:School)
                CREATE (event:Event {
                    EventID: $event_id,
                    Title: $title,
                    Description: $description,
                    Picture: $image,
                    Location: $location,
                    StartDateTime: datetime($start_date_time),
                    EndDateTime: datetime($end_date_time),
                    Visibility: $visibility,
                    TimeCreated: datetime()
                })<-[:user_host]-(user),
                (event)-[:event_school]->(school)
                WITH user, event
                UNWIND $interest_ids as interest_id
                MATCH (tag:Interest {InterestID: interest_id})
                CREATE (tag)<-[:event_tag]-(event)""",
            parameters={
                "event_id": event_id,
                "user_access_token": user_access_token,
                "image": event_image,
                "title": title,
                "description": description,
                "location": location,
                "start_date_time": start_date_time,
                "end_date_time": end_date_time,
                "visibility": visibility,
                "interest_ids": interest_ids,
            },
        )

    return event_id
