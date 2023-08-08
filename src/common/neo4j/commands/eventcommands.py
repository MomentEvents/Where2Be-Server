from common.neo4j.converters import convert_event_entity_to_event
from common.neo4j.moment_neo4j import parse_neo4j_data, run_neo4j_query
from common.s3.moment_s3 import get_bucket_url
from common.models import Problem
from dateutil import parser
import secrets
import random
from datetime import datetime


async def create_event_entity(event_id: str, user_access_token: str, event_image: str, title: str, description: str, location: str, visibility: str, interest_ids, start_date_time_string, end_date_time_string):
    start_date_time = parser.parse(start_date_time_string)
    end_date_time = None if end_date_time_string is None else parser.parse(
        end_date_time_string)

    title = title.strip()
    description = description.strip()
    location = location.strip()
    if (event_id is None):
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
            })<-[rel:user_host]-(user),
            (event)-[:event_school]->(school)
            SET rel.IsNotified = false
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


async def get_event_entity_by_event_id(event_id: str, user_access_token=None):

    if (user_access_token):

        result = await run_neo4j_query(
            """MATCH (event:Event{EventID : $event_id}), (user:User{UserAccessToken:$user_access_token}), (event)<-[:user_host]-(host:User)
                WITH (event),
                    COUNT{(event)<-[:user_join]-()} as num_joins,
                    COUNT{(event)<-[:user_shoutout]-()} as num_shoutouts,
                    exists((event)<-[:user_join]-(user)) as user_join,
                    exists((event)<-[:user_shoutout]-(user)) as user_shoutout,
                    host.UserID as host_user_id
                RETURN{
                    EventID: event.EventID,
                    Title: event.Title,
                    Description: event.Description,
                    StartDateTime: event.StartDateTime,
                    EndDateTime: event.EndDateTime,
                    Picture: event.Picture,
                    Visibility: event.Visibility,
                    SignupLink: event.SignupLink,
                    Location: event.Location,
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

        data = parse_neo4j_data(result, 'single')

        if (data is None):
            return None

        event_data = convert_event_entity_to_event(data)

        return event_data

    else:
        result = await run_neo4j_query(
            """MATCH (event:Event{EventID : $event_id}), (event)<-[:user_host]-(host:User)
                WITH (event),
                    COUNT{(event)<-[:user_join]-()} as num_joins,
                    COUNT{(event)<-[:user_shoutout]-()} as num_shoutouts,
                    host.UserID as host_user_id
                RETURN{
                    EventID: event.EventID,
                    Title: event.Title,
                    Description: event.Description,
                    StartDateTime: event.StartDateTime,
                    EndDateTime: event.EndDateTime,
                    Picture: event.Picture,
                    Visibility: event.Visibility,
                    SignupLink: event.SignupLink,
                    Location: event.Location,
                    num_joins: num_joins,
                    num_shoutouts: num_shoutouts,
                    user_join: False,
                    user_shoutout: False,
                    host_user_id: host_user_id
                }""",
            parameters={
                "event_id": event_id
            },
        )

        data = parse_neo4j_data(result, 'single')

        if (data is None):
            return None

        event_data = convert_event_entity_to_event(data)

        return event_data


async def get_and_notify_all_starting_soon_events(lookahead_period_min: int):

    event_data = dict()

    result = await run_neo4j_query(
        """
        MATCH (e:Event)-[rel:user_join|user_host]-(u:User)
        WHERE datetime(e.StartDateTime) >= datetime() AND datetime(e.StartDateTime) <= datetime() + duration({minutes: $lookahead_period_min}) 
        AND (type(rel) = 'user_join' OR type(rel) = 'user_host') AND rel.IsNotified = false
        UNWIND u.PushTokens AS pushTokensList
        RETURN e.Title AS title, e.EventID AS event_id, COLLECT(DISTINCT {token: pushTokensList, user_id: u.UserID}) AS user_details""",
        parameters={
            "lookahead_period_min": lookahead_period_min,
        }
    )

    for record in result:
        event_id = record['event_id']
        if event_id not in event_data:
            event_data[event_id] = [record['title'], record['user_details']]

    # print(event_data)
    return event_data


async def get_random_popular_event_within_x_days(days: int, school_id: str):

    result = await run_neo4j_query("""MATCH (e:Event)-[:event_school]->(school:School{SchoolID: $school_id}), (e)<-[:user_host]-(host:User)
            WHERE e.StartDateTime <= datetime() + duration({days: $days})
            WITH e, host, COUNT{(e)<-[:user_join]-()} as num_joins, COUNT{(e)<-[:user_shoutout]-()} as num_shoutouts,exists((:User)-[:user_shoutout]->(e)) as user_shoutout
            WITH num_joins + num_shoutouts as popularity, num_joins, num_shoutouts, e, host
            ORDER BY popularity DESC
            LIMIT 15
            WITH collect({
                host_displayName: host.DisplayName,
                host_username: host.Username,
                host_picture: host.Picture,
                VerifiedOrganization: host.VerifiedOrganization,
                EventID: e.EventID,
                Title: e.Title,
                Picture: e.Picture,
                Description: e.Description,
                Location: e.Location,
                StartDateTime: e.StartDateTime,
                EndDateTime: e.EndDateTime,
                Visibility: e.Visibility,
                num_joins: num_joins,
                num_shoutouts: num_shoutouts,
                host_user_id: host.UserID
                }) AS popular_events
            UNWIND apoc.coll.shuffle(popular_events)[0] AS result
            RETURN result""",
                                   parameters={
                                       "school_id": school_id,
                                       "days": days
                                   }
                                   )

    data = parse_neo4j_data(result, 'single')

    if (data is None):
        return None

    event_data = convert_event_entity_to_event(data)

    return event_data


async def get_events_created_after_given_time(given_time):
    # Format the datetime object to a string in the correct format
    if isinstance(given_time, str):
        datetime_object = datetime.strptime(
            given_time, "%Y-%m-%dT%H:%M:%S.%f")  # try to generalize this
        formatted_time = datetime_object.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    else:
        formatted_time = given_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    result = await run_neo4j_query("""MATCH (e:Event) WHERE e.TimeCreated >= datetime($formatted_time) RETURN e""",
                                   parameters={
                                       "formatted_time": formatted_time
                                   }
                                   )

    event_array = []
    for record in result:
        if record == None:
            return []
        data = record['e']
        event_array.append(convert_event_entity_to_event(data))

    return event_array


async def user_isnotified(user_id, event_id):
    print("Notified for", user_id, "for event", event_id)

    query = """
    MATCH (u:User {UserID: $user_id})-[rel:user_join|user_host]-(e:Event {EventID: $event_id})
    SET rel.IsNotified = True
    """

    parameters = {
        "user_id": user_id,
        "event_id": event_id
    }

    await run_neo4j_query(query, parameters)

    return 0
