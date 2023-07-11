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

def get_event_entity_by_event_id(event_id: str, user_access_token: str):

    with get_neo4j_session() as session:

        result = session.run(
                """MATCH (event:Event{EventID : $event_id}), (user:User{UserAccessToken:$user_access_token}), (event)<-[:user_host]-(host:User)
                WITH (event),
                    size ((event)<-[:user_join]-()) as num_joins,
                    size ((event)<-[:user_shoutout]-()) as num_shoutouts,
                    exists ((event)<-[:user_join]-(user)) as user_join,
                    exists ((event)<-[:user_shoutout]-(user)) as user_shoutout,
                    host.UserID as host_user_id
                RETURN{
                    event_id: event.EventID,
                    title: event.Title,
                    description: event.Description,
                    start_date_time: event.StartDateTime,
                    end_date_time: event.EndDateTime,
                    picture: event.Picture,
                    visibility: event.Visibility,
                    location: event.Location,
                    num_joins: num_joins,
                    num_shoutouts: num_shoutouts,
                    user_join: user_join,
                    user_shoutout: user_shoutout,
                    host_user_id: host_user_id
                }""",
            parameters={
                "event_id": event_id,
                "user_access_token": user_access_token,
            },
        )

        # get the first element of object
        record = result.single()

        if record == None:
            return None

        data = record[0]
        print(data["end_date_time"])
        
        event_data = {
            "event_id": data["event_id"],
            "picture": data["picture"],
            "title": data["title"],
            "description": data["description"],
            "location": data["location"],
            "start_date_time": str(data["start_date_time"]),
            "end_date_time": None if data["end_date_time"] == "NULL" else str(data["end_date_time"]),
            "visibility": data["visibility"],
            "num_joins": data["num_joins"],
            "num_shoutouts": data["num_shoutouts"],
            "user_join": data["user_join"],
            "user_shoutout": data["user_shoutout"],
            "host_user_id": data["host_user_id"],
        }

        return event_data