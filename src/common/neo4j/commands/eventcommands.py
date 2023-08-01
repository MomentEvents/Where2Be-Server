from common.neo4j.moment_neo4j import get_neo4j_session, parse_neo4j_data, run_neo4j_query
from common.s3.moment_s3 import get_bucket_url
from common.models import Problem
from dateutil import parser
import secrets
import random

async def create_event_entity(event_id: str, user_access_token: str, event_image: str, title: str, description: str, location: str, visibility: str, interest_ids, start_date_time_string, end_date_time_string):
    start_date_time = parser.parse(start_date_time_string)
    end_date_time = None if end_date_time_string is None else parser.parse(end_date_time_string)


    title = title.strip()
    description = description.strip()
    location = location.strip()
    if(event_id is None):
        event_id = secrets.token_urlsafe()



    result = await run_neo4j_query(
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

async def get_event_entity_by_event_id(event_id: str, user_access_token: str):

    result = await run_neo4j_query(
            """MATCH (event:Event{EventID : $event_id}), (user:User{UserAccessToken:$user_access_token}), (event)<-[:user_host]-(host:User)
            WITH (event),
                COUNT{(event)<-[:user_join]-()} as num_joins,
                COUNT{(event)<-[:user_shoutout]-()} as num_shoutouts,
                exists((event)<-[:user_join]-(user)) as user_join,
                exists((event)<-[:user_shoutout]-(user)) as user_shoutout,
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
                host_user_id: host_user_id,
                signup_link: e.SignupLink
            }""",
        parameters={
            "event_id": event_id,
            "user_access_token": user_access_token,
            },
        )

    data = parse_neo4j_data(result, 'single')

    if(data is None):
        return None
    
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
    
async def get_random_popular_event_within_x_days(days: int, school_id: str):

    result = await run_neo4j_query("""MATCH (e:Event)-[:event_school]->(school:School{SchoolID: $school_id}), (e)<-[:user_host]-(host:User)
            WHERE e.StartDateTime <= datetime() + duration({days: $days})
            WITH e, host, COUNT{(e)<-[:user_join]-()} as num_joins, COUNT{(e)<-[:user_shoutout]-()} as num_shoutouts, exists((:User{UserAccessToken: $user_access_token})-[:user_follow]->(host)) as user_follow_host,
                exists((:User{UserAccessToken: $user_access_token})-[:user_join]->(e)) as user_join,
                exists((:User{UserAccessToken: $user_access_token})-[:user_shoutout]->(e)) as user_shoutout
            WITH num_joins + num_shoutouts as popularity, num_joins, num_shoutouts, e, host, user_join, user_shoutout, user_follow_host
            ORDER BY popularity DESC
            LIMIT 30
            WITH collect({
                user_id: host.UserID, 
                display_name: host.DisplayName,
                username: host.Username,
                host_picture: host.Picture,
                verified_organization: host.VerifiedOrganization,
                event_id: e.EventID,
                title: e.Title,
                event_picture: e.Picture,
                description: e.Description,
                location: e.Location,
                start_date_time: e.StartDateTime,
                end_date_time: e.EndDateTime,
                visibility: e.Visibility,
                num_joins: num_joins,
                num_shoutouts: num_shoutouts,
                user_join: user_join,
                user_shoutout: user_shoutout,
                host_user_id: host.UserID,
                user_follow_host: user_follow_host,
                signup_link: e.SignupLink
                }) AS popular_events
            UNWIND apoc.coll.shuffle(popular_events)[0] AS result
            RETURN result
            }""",
        parameters={
            "school_id": school_id,
            "days": days
        },
    )

    data = parse_neo4j_data(result, 'single')

    if(data is None):
        return None

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