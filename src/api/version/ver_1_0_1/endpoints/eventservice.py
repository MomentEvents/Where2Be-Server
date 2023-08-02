from inspect import Parameter

from markupsafe import string
from common.firebase import create_firestore_document, create_firestore_event_message, delete_firestore_event_message, get_firebase_user_by_uid, get_firestore_document, send_verification_email
from common.models import Problem
from common.neo4j.commands.eventcommands import create_event_entity, get_event_entity_by_event_id
from common.neo4j.commands.notificationcommands import get_all_follower_push_tokens, get_all_joined_users_push_tokens
from common.neo4j.commands.usercommands import get_user_entity_by_user_access_token, get_user_entity_by_user_id
from common.utils import send_and_validate_expo_push_notifications
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.background import BackgroundTasks
import time




# from datetime import datetime
from dateutil import parser
import bcrypt
import secrets
import random

from common.neo4j.moment_neo4j import get_neo4j_session
from api.version.ver_1_0_1.auth import is_real_user, is_requester_privileged_for_event, is_requester_privileged_for_user, is_event_formatted, is_real_event, is_picture_formatted, is_valid_user_access_token
from api.helpers import parse_request_data

from common.s3.moment_s3 import upload_base64_image


import platform

from io import BytesIO
import io

import boto3

import base64
from PIL import Image
import json
import cv2
import numpy as np
from common.constants import IS_PROD, SCRAPER_TOKEN


@is_picture_formatted
@is_event_formatted
async def create_event(request: Request) -> JSONResponse:
    """
    Description: Creates an event associated with the user in the user_access_token. Returns an error if too many events are created at the same time from that same user (for spam)

    params:
        user_access_token: string,
        title: string,
        description: string,
        location: string,
        start_date_time: string,
        end_date_time: string,
        visibility: boolean,
        interest_id: string[],
        picture: string,
        ping_followers: boolean,

    return:
        event_id: string

    """

    request_data = await parse_request_data(request)

    end_date_time = None
    user_access_token = request_data.get("user_access_token")
    scraper_token = request_data.get("scraper_token")

    if(user_access_token is None):
        raise Problem(status=400, content="No user_access_token has been passed in.")
    
    request.state.background = BackgroundTasks()

    user = get_user_entity_by_user_access_token(user_access_token, False)
    if(IS_PROD and scraper_token != SCRAPER_TOKEN):

        firebase_user = get_firebase_user_by_uid(user['user_id'])
        if(firebase_user.email_verified is None or firebase_user.email_verified is False):
            try:
                request.state.background.add_task(send_verification_email, firebase_user.email)
            except:
                print("UNABLE TO SEND VERIFICATION EMAIL")
            return Response(status_code=400, content="You must verify your email before you can post events. Check " + firebase_user.email, background=request.state.background)

    title = request_data.get("title")
    description = request_data.get("description")
    location = request_data.get("location")
    start_date_time = request_data.get("start_date_time")
    end_date_time = request_data.get("end_date_time")
    visibility = request_data.get("visibility")
    interest_ids = [*set(json.loads(request_data.get("interest_ids")))]
    picture = request_data.get("picture")

    ping_followers = True if request_data.get("ping_followers") == "true" else False

    try:
        assert({ping_followers})
        assert type(ping_followers) == bool
    except AssertionError:
        return Response(status_code=400, content="Incomplete body or incorrect parameter")

    event_id = secrets.token_urlsafe()   
    image_id = secrets.token_urlsafe()
    event_image = await upload_base64_image(picture, "app-uploads/images/events/event-id/"+event_id+"/", image_id)
    title = title.strip()
    location = location.strip()

    event_id = create_event_entity(event_id, user_access_token, event_image, title, description, location, visibility, interest_ids, start_date_time, end_date_time)

    event_data = {
        "event_id": str(event_id),
    }

    if(ping_followers):
        print("PINGING FOLLOWERS")
        try:
            follower_push_tokens_with_user_id = get_all_follower_push_tokens(user['user_id'])
            if(follower_push_tokens_with_user_id is not None):
                request.state.background.add_task(send_and_validate_expo_push_notifications, follower_push_tokens_with_user_id, "New event posted", "" + str(user["username"] + " just posted \"" + str(title)) + "\"", {
                        'action': 'ViewEventDetails',
                        'event_id': event_id,
                    })
        except Exception as e:
            print("ERROR SENDING FOLLOWER PUSH NOTIFICATION: \n\n" + str(e))
    
    return JSONResponse(event_data, background=request.state.background)

async def get_event(request: Request) -> JSONResponse:
    """
    Description: Gets an event with an event_id of {event_id}. We send a user_access_token to verify that the user has authorization to view the event (if it is private or not). If it is private, it is only viewable when the user_access_token is the owner of the event.

    params:
        user_access_token: string

    return:
        event_id: string,
        title: string,
        description: string,
        picture: string,
        location: string,
        start_date_time: string,
        end_date_time: string,
        visibility: boolean,
        interest_id: string[]
    """

    event_id = request.path_params["event_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")

    try:
        assert all((user_access_token))
    except AssertionError:
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Parameter Missing")

    print("about to go to connection")

    event_data = get_event_entity_by_event_id(event_id, user_access_token)

    if(event_data == None):
        return Response(status_code=400, content="Event does not exist")

    return JSONResponse(event_data)

@is_real_event
@is_requester_privileged_for_event
async def delete_event(request: Request) -> JSONResponse:
    """
    Description: Deletes an event with an event_id of {event_id}. This returns a valid response when the user_access_token is the owner of the event. Error when the user is not the owner of the event

    params:
        user_access_token: string

    """
    event_id = request.path_params["event_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")

    with get_neo4j_session() as session:
        # check if email exists
        result = session.run(
            """MATCH (e:Event{EventID : $event_id})
            DETACH DELETE e""",
            parameters={
                "user_access_token": user_access_token,
                "event_id": event_id,
            },
        )

    return Response(status_code=200, content="event deleted " + event_id)

@is_event_formatted
@is_real_event
@is_requester_privileged_for_event
async def update_event(request: Request) -> JSONResponse:
    """
    Description: Updates an event with an event_id of {event_id}. This returns a valid response when the user_access_token is the owner of the event. Error when the user is not the owner of the event

    params:
        user_access_token: string,
        title: string | null,
        description: string | null,
        location: string | null,
        start_date_time: Date(?) | null,
        end_date_time: Date(?) | null,
        visibility: boolean | null,
        ping_joined_users: bool,

    return:

    """
    request.state.background = BackgroundTasks()


    event_id = request.path_params["event_id"]

    request_data = await parse_request_data(request)

    user_access_token = request_data["user_access_token"]
    title = request_data["title"]
    description = request_data["description"]
    location = request_data["location"]
    start_date_time = parser.parse(request_data["start_date_time"])
    end_date_time = None if request_data["end_date_time"] is None else parser.parse(request_data["end_date_time"])
    visibility = request_data["visibility"]
    interest_ids = [*set(json.loads(request_data["interest_ids"]))]
    picture = request_data["picture"]
    
    ping_joined_users = True if request_data.get("ping_joined_users") == "true" else False
    try:
        assert type(ping_joined_users) == bool
    except AssertionError:
        return Response(status_code=400, content="Incomplete body or incorrect parameter")

    print(event_id)

    event_image = None
    if picture != "null" and picture != "undefined":
        image_id = secrets.token_urlsafe()
        event_image = await upload_base64_image(picture, "app-uploads/images/events/event-id/"+event_id+"/", image_id)
    else:
        picture = None

    title = title.strip()
    location = location.strip()

    with get_neo4j_session() as session:
        result = session.run(
            """MATCH (e:Event{EventID : $event_id})-[r:event_tag]->(i:Interest), (en:Event{EventID: $event_id})
            DELETE r
            WITH en
            UNWIND $interest_ids as interest_id
            MERGE (i:Interest{InterestID: interest_id})
            CREATE (en)-[:event_tag]->(i)
            SET 
                en.Title = COALESCE($title, en.Title),
                en.Description = COALESCE($description, en.Description),
                en.Picture = COALESCE($image, en.Picture),
                en.Location = COALESCE($location, en.Location),
                en.StartDateTime = COALESCE($start_date_time, en.StartDateTime),
                en.EndDateTime = COALESCE($end_date_time, en.EndDateTime),
                en.Visibility = COALESCE($visibility, en.Visibility),
                en.TimeCreated = datetime()
            RETURN{
                    title: en.Title
                }
            """,
            parameters={
                "event_id": event_id,
                "title": title,
                "description": description,
                "image": event_image,
                "location": location,
                "start_date_time": start_date_time,
                "end_date_time": end_date_time,
                "visibility": visibility,
                "interest_ids": interest_ids,
            },
        )
        # get the first element of object
        record = result.single()

        if record == None:
            return None

        data = record[0]
        new_title = data["title"]

        if(ping_joined_users):
            print("PINGING JOINED USERS")
            user = get_user_entity_by_user_access_token(user_access_token=user_access_token, show_num_events_followers_following=False)
            try:
                joined_users_push_tokens_with_user_id = get_all_joined_users_push_tokens(event_id)
                print(joined_users_push_tokens_with_user_id)
                if(joined_users_push_tokens_with_user_id is not None):
                    request.state.background.add_task(
                        send_and_validate_expo_push_notifications, 
                        joined_users_push_tokens_with_user_id, 
                        "Event updated", 
                        str(user['username']) + " changed details for \"" + str(new_title) + "\"", 
                        {
                            'action': 'ViewEventDetails',
                            'event_id': event_id,
                        }
                    )
            except Exception as e:
                print("ERROR SENDING FOLLOWER PUSH NOTIFICATION: \n\n" + str(e))
    return Response(status_code=200, content="event updated", background=request.state.background)

async def get_events_categorized(request: Request) -> JSONResponse:
    """
    Description: Gets all events attached to a school of {school_id} for introduce events. user_join and user_shoutout are defaulted to be false

    params:

    return:
        "Featured": 
        [{
			event_id: string,
			title: string,
			picture: string,
			description: string,
			location: string,
			start_date_time: string (convert to Date),
			end_date_time: string (convert to Date),
			visibility: boolean,
			num_joins: int  
			num_shoutouts: int
			user_join: boolean
			user_shoutout: boolean
        }]
    """
    school_id = request.path_params.get("school_id")

    request_data = await parse_request_data(request)

    user_access_token = request_data.get("user_access_token")

    try:
        assert all({user_access_token, school_id})
    except:
        Response(status_code=400, content="Incomplete body")

    with get_neo4j_session() as session:

        if user_access_token == None:
            result = session.run(
                """MATCH (e:Event)-[:event_school]->(school:School {SchoolID: $school_id}),(e)<-[:user_host]-(host:User)
                WITH DISTINCT e,
                    COUNT{ (e)<-[:user_join]-() } as num_joins,
                    COUNT{ (e)<-[:user_shoutout]-() } as num_shoutouts,
                    host.UserID as host_user_id
                WHERE e.Featured IS NOT NULL AND e.Featured = true AND (datetime() > e.StartDateTime)
                WITH
                    { 
                        event_id: e.EventID,
                        title: e.Title,
                        picture: e.Picture,
                        description: e.Description,
                        location: e.Location,
                        start_date_time: e.StartDateTime,
                        end_date_time: e.EndDateTime,
                        visibility: e.Visibility,
                        num_joins: num_joins,
                        num_shoutouts: num_shoutouts,
                        user_join: False,
                        user_shoutout: False,
                        host_user_id: host_user_id
                    } as event
                ORDER BY num_joins+num_shoutouts DESC
                LIMIT 10
                WITH collect(event) as events
                RETURN apoc.map.setKey({}, "Featured", events) as event_dict
                
                UNION

                MATCH (e:Event)-[:event_school]->(school:School {SchoolID: $school_id}),(e)<-[:user_host]-(host:User)
                WITH DISTINCT e,
                    COUNT{ (e)<-[:user_join]-() } as num_joins,
                    COUNT{ (e)<-[:user_shoutout]-() } as num_shoutouts,
                    host.UserID as host_user_id
                WHERE (datetime() < e.EndDateTime) AND (datetime() > e.StartDateTime)
                WITH
                    { 
                        event_id: e.EventID,
                        title: e.Title,
                        picture: e.Picture,
                        description: e.Description,
                        location: e.Location,
                        start_date_time: e.StartDateTime,
                        end_date_time: e.EndDateTime,
                        visibility: e.Visibility,
                        num_joins: num_joins,
                        num_shoutouts: num_shoutouts,
                        user_join: False,
                        user_shoutout: False,
                        host_user_id: host_user_id
                    } as event
                ORDER BY num_joins+num_shoutouts DESC
                LIMIT 10
                WITH collect(event) as events
                RETURN apoc.map.setKey({}, "Ongoing", events) as event_dict

                UNION
                
                MATCH (e:Event)-[:event_school]->(school:School {SchoolID: $school_id}), (e)-[:event_tag]->(i:Interest), (e)<-[:user_host]-(host:User)
                WITH DISTINCT e, i,
                    COUNT{ (e)<-[:user_join]-() } as num_joins,
                    COUNT{ (e)<-[:user_shoutout]-() } as num_shoutouts,
                    host.UserID as host_user_id
                WHERE e.StartDateTime >= datetime()
                WITH i.Name as interest,
                { 
                    event_id: e.EventID,
                    title: e.Title,
                    picture: e.Picture,
                    description: e.Description,
                    location: e.Location,
                    start_date_time: e.StartDateTime,
                    end_date_time: e.EndDateTime,
                    visibility: e.Visibility,
                    num_joins: num_joins,
                    num_shoutouts: num_shoutouts,
                    user_join: False,
                    user_shoutout: False,
                    host_user_id: host_user_id
                } as event
                ORDER BY e.StartDateTime
                WITH interest, collect(event) as events
                ORDER BY interest
                RETURN apoc.map.setKey({}, interest, events) as event_dict
                """,
                parameters={
                    "school_id": school_id,
                    "user_access_token": user_access_token
                },
            )
        else:
            result = session.run(
                """
                MATCH (e:Event)-[:event_school]->(school:School {SchoolID: $school_id}),(u:User{UserAccessToken: $user_access_token}),(e)<-[:user_host]-(host:User)
                WITH DISTINCT e,
                    COUNT{ (e)<-[:user_join]-() } as num_joins,
                    COUNT{ (e)<-[:user_shoutout]-() } as num_shoutouts,
                    exists((u)-[:user_join]->(e)) as user_join,
                    exists((u)-[:user_shoutout]->(e)) as user_shoutout,
                    host.UserID as host_user_id
                WHERE e.Featured IS NOT NULL AND e.Featured = true AND (datetime() > e.StartDateTime)
                WITH
                    { 
                        event_id: e.EventID,
                        title: e.Title,
                        picture: e.Picture,
                        description: e.Description,
                        location: e.Location,
                        start_date_time: e.StartDateTime,
                        end_date_time: e.EndDateTime,
                        visibility: e.Visibility,
                        num_joins: num_joins,
                        num_shoutouts: num_shoutouts,
                        user_join: False,
                        user_shoutout: False,
                        host_user_id: host_user_id
                    } as event
                ORDER BY num_joins+num_shoutouts DESC
                LIMIT 10
                WITH collect(event) as events
                RETURN apoc.map.setKey({}, "Featured", events) as event_dict
                
                UNION
                
                MATCH (e:Event)-[:event_school]->(school:School {SchoolID: $school_id}),(u:User{UserAccessToken: $user_access_token}),(e)<-[:user_host]-(host:User)
                WITH DISTINCT e,
                    COUNT{ (e)<-[:user_join]-() } as num_joins,
                    COUNT{ (e)<-[:user_shoutout]-() } as num_shoutouts,
                    exists((u)-[:user_join]->(e)) as user_join,
                    exists((u)-[:user_shoutout]->(e)) as user_shoutout,
                    host.UserID as host_user_id
                WHERE (datetime() < e.EndDateTime) AND (datetime() > e.StartDateTime)
                WITH
                    { 
                        event_id: e.EventID,
                        title: e.Title,
                        picture: e.Picture,
                        description: e.Description,
                        location: e.Location,
                        start_date_time: e.StartDateTime,
                        end_date_time: e.EndDateTime,
                        visibility: e.Visibility,
                        num_joins: num_joins,
                        num_shoutouts: num_shoutouts,
                        user_join: user_join,
                        user_shoutout: user_shoutout,
                        host_user_id: host_user_id
                    } as event
                ORDER BY num_joins+num_shoutouts DESC
                LIMIT 10
                WITH collect(event) as events
                RETURN apoc.map.setKey({}, "Ongoing", events) as event_dict

                UNION
                
                MATCH (e:Event)-[:event_school]->(school:School {SchoolID: $school_id}), (e)-[:event_tag]->(i:Interest), (u:User{UserAccessToken: $user_access_token}), (e)<-[:user_host]-(host:User)
                WITH DISTINCT e, i,
                    COUNT{ (e)<-[:user_join]-() } as num_joins,
                    COUNT{ (e)<-[:user_shoutout]-() } as num_shoutouts,
                    exists((u)-[:user_join]->(e)) as user_join,
                    exists((u)-[:user_shoutout]->(e)) as user_shoutout,
                    host.UserID as host_user_id
                WHERE e.StartDateTime >= datetime()
                WITH i.Name as interest,
                { 
                    event_id: e.EventID,
                    title: e.Title,
                    picture: e.Picture,
                    description: e.Description,
                    location: e.Location,
                    start_date_time: e.StartDateTime,
                    end_date_time: e.EndDateTime,
                    visibility: e.Visibility,
                    num_joins: num_joins,
                    num_shoutouts: num_shoutouts,
                    user_join: user_join,
                    user_shoutout: user_shoutout,
                    host_user_id: host_user_id
                } as event
                ORDER BY e.StartDateTime
                LIMIT 10
                WITH interest, collect(event) as events
                ORDER BY interest
                RETURN apoc.map.setKey({}, interest, events) as event_dict
                """,
                parameters={
                    "school_id": school_id,
                    "user_access_token": user_access_token
                },
            )

        categorized_dict = {}
        event_ids = []
        for record in result:
            print("record: ",record)
            interest_data = record['event_dict']
            for interest in interest_data:
                events = []
                events_data = interest_data[interest]
                for event_data in events_data:
                    event_id = event_data['event_id']
                    title = event_data['title']
                    picture = event_data['picture']
                    description = event_data['description']
                    location = event_data['location']
                    start_date_time = str(event_data['start_date_time'])
                    end_date_time = None if event_data["end_date_time"] == "NULL" else str(event_data["end_date_time"])
                    visibility = event_data['visibility']
                    num_joins = event_data['num_joins']
                    num_shoutouts = event_data['num_shoutouts']
                    user_join = event_data['user_join']
                    user_shoutout = event_data['user_shoutout']
                    host_user_id = event_data['host_user_id']

                    if (event_id not in event_ids): # or (interest == "Featured" ):

                        # if interest != "Featured":
                        event_ids.append(event_id) 

                        events.append({
                            'event_id': event_id,
                            'title': title,
                            'picture': picture,
                            'description': description,
                            'location': location,
                            'start_date_time': start_date_time,
                            'end_date_time': end_date_time,
                            'visibility': visibility,
                            'num_joins': num_joins,
                            'num_shoutouts': num_shoutouts,
                            'user_join': user_join,
                            'user_shoutout': user_shoutout,
                            'host_user_id': host_user_id,
                        })

                if events!= []:
                    categorized_dict[interest] = events

        return JSONResponse(categorized_dict)

async def search_events(request: Request) -> JSONResponse:
    """
    Description: Searches events in a query

    params:

    return:
        [{
                        event_id: string,
                        title: string,
                        picture: string,
                        description: string,
                        location: string,
                        start_date_time: string (convert to Date),
                        end_date_time: string (convert to Date),
                        visibility: boolean,
                        num_joins: int  
                        num_shoutouts: int
                        user_join: boolean
                        user_shoutout: boolean
        }]
    """
    school_id = request.path_params["school_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")
    query = body.get("query")
    try:
        assert all({user_access_token, school_id, query})
    except:
        return Response(status_code=400, content="Incomplete body")

    query = query.strip()

    with get_neo4j_session() as session:
        # check if email exists
        result = session.run(
    """
    MATCH (e:Event)-[:event_school]->(school: School{SchoolID: $school_id})
    MATCH (e)<-[:user_host]-(host:User)
    MATCH (u:User{UserAccessToken: $user_access_token})
    WITH DISTINCT e,
        COUNT{(e)<-[:user_join]-()} as num_joins,
        COUNT{(e)<-[:user_shoutout]-()} as num_shoutouts,
        exists((u)-[:user_join]->(e)) as user_join,
        exists((u)-[:user_shoutout]->(e)) as user_shoutout,
        host.UserID as host_user_id
    WHERE e.StartDateTime >= datetime() AND (toLower(e.Title) CONTAINS toLower($query) OR toLower(e.Location) CONTAINS toLower($query))
    RETURN { event_id: e.EventID,
            title: e.Title,
            picture: e.Picture,
            description: e.Description,
            location: e.Location,
            start_date_time: e.StartDateTime,
            end_date_time: e.EndDateTime,
            visibility: e.Visibility,
            num_joins: num_joins,
            num_shoutouts: num_shoutouts,
            user_join: user_join,
            user_shoutout: user_shoutout,
            host_user_id: host_user_id } as event
    ORDER BY toLower(e.Title)
    LIMIT 20
    """,
            parameters={
                "school_id": school_id,
                "query": query,
                "user_access_token": user_access_token,
            },
        )

        events = []
        for record in result:
            event_data = record['event']
            event_id = event_data['event_id']
            title = event_data['title']
            picture = event_data['picture']
            description = event_data['description']
            location = event_data['location']
            start_date_time = str(event_data['start_date_time'])
            end_date_time = None if event_data["end_date_time"] == "NULL" else str(
                event_data["end_date_time"]),
            visibility = event_data['visibility']
            num_joins = event_data['num_joins']
            num_shoutouts = event_data['num_shoutouts']
            user_join = event_data['user_join']
            user_shoutout = event_data['user_shoutout']
            host_user_id = event_data['host_user_id']

            events.append({
                'event_id': event_id,
                'title': title,
                'picture': picture,
                'description': description,
                'location': location,
                'start_date_time': start_date_time,
                'end_date_time': end_date_time,
                'visibility': visibility,
                'num_joins': num_joins,
                'num_shoutouts': num_shoutouts,
                'user_join': user_join,
                'user_shoutout': user_shoutout,
                'host_user_id': host_user_id
            })

        return JSONResponse(events)


 
async def host_past(request: Request) -> JSONResponse:

    print("CALLED host_past")
    begin_start_time = time.perf_counter()


    user_id = request.path_params["user_id"]

    body = await request.json()
    user_access_token = body["user_access_token"]
    cursor_event_id = body.get("cursor_event_id", None)
    cursor_start_date_time = body.get("cursor_start_date_time", None)

    try:
        assert all({user_access_token, user_id})
    except:
        Response(status_code=400, content="Incomplete body")

    cursor_clause = ""
    if cursor_event_id and cursor_start_date_time:
        cursor_clause = "AND (e.StartDateTime < datetime($cursor_start_date_time) OR (e.StartDateTime = datetime($cursor_start_date_time) AND e.EventID < $cursor_event_id))"

    query = f"""MATCH ((e:Event)-[:user_host]-(u:User{{UserID:$user_id}})), (c:User{{UserAccessToken: $user_access_token}})
                WITH DISTINCT e,
                    COUNT{{ (e)<-[:user_join]-() }} as num_joins,
                    COUNT{{ (e)<-[:user_shoutout]-() }} as num_shoutouts,
                    exists((c)-[:user_join]->(e)) as user_join,
                    exists((c)-[:user_shoutout]->(e)) as user_shoutout
                WHERE e.StartDateTime < datetime() {cursor_clause}
                RETURN {{ event_id: e.EventID,
                        title: e.Title,
                        picture: e.Picture,
                        description: e.Description,
                        location: e.Location,
                        start_date_time: e.StartDateTime,
                        end_date_time: e.EndDateTime,
                        visibility: e.Visibility,
                        num_joins: num_joins,
                        num_shoutouts: num_shoutouts,
                        user_join: user_join,
                        user_shoutout: user_shoutout,
                        host_user_id: $user_id }} as event
                ORDER BY e.StartDateTime DESC, e.EventID DESC
                LIMIT 20
                """

    parameters={
        "user_id": user_id,
        "user_access_token": user_access_token,
        "cursor_event_id": cursor_event_id,
        "cursor_start_date_time": cursor_start_date_time
        }

    start_time = time.perf_counter()

    data = get_event_list_from_query(query, parameters)

    end_time = time.perf_counter()
    elapsed_time_ms = (end_time - start_time) * 1000  # convert to milliseconds

    print("took ", str(elapsed_time_ms), " milliseconds for host past") 

    elapsed_time_ms = (start_time - begin_start_time) * 1000  # convert to milliseconds

    print("took ", str(elapsed_time_ms), " milliseconds before calling query to get host past") 


    return data

 
async def host_future(request: Request) -> JSONResponse:


    print("CALLING host_future")
    begin_start_time = time.perf_counter()

    
    user_id = request.path_params["user_id"]

    body = await request.json()
    user_access_token = body["user_access_token"]
    cursor_event_id = body.get("cursor_event_id", None)
    cursor_start_date_time = body.get("cursor_start_date_time", None)

    try:
        assert all({user_access_token, user_id})
    except:
        Response(status_code=400, content="Incomplete body")

    print(cursor_event_id)
    print(cursor_start_date_time)
    cursor_clause = ""
    if cursor_event_id and cursor_start_date_time:
        print("GOING INTO CURSOR CLAUSE")
        cursor_clause = "AND (e.StartDateTime > datetime($cursor_start_date_time) OR (e.StartDateTime = datetime($cursor_start_date_time) AND e.EventID > $cursor_event_id))"

    query = f"""MATCH ((e:Event)-[:user_host]-(u:User{{UserID:$user_id}})), (c:User{{UserAccessToken: $user_access_token}})
                WITH DISTINCT e,
                    COUNT{{ (e)<-[:user_join]-() }} as num_joins,
                    COUNT{{ (e)<-[:user_shoutout]-() }} as num_shoutouts,
                    exists((c)-[:user_join]->(e)) as user_join,
                    exists((c)-[:user_shoutout]->(e)) as user_shoutout
                WHERE e.StartDateTime >= datetime() {cursor_clause}
                RETURN {{ event_id: e.EventID,
                        title: e.Title,
                        picture: e.Picture,
                        description: e.Description,
                        location: e.Location,
                        start_date_time: e.StartDateTime,
                        end_date_time: e.EndDateTime,
                        visibility: e.Visibility,
                        num_joins: num_joins,
                        num_shoutouts: num_shoutouts,
                        user_join: user_join,
                        user_shoutout: user_shoutout,
                        host_user_id: $user_id }} as event
                ORDER BY e.StartDateTime ASC, e.EventID ASC
                LIMIT 20
                """

    parameters={
        "user_id": user_id,
        "user_access_token": user_access_token,
        "cursor_event_id": cursor_event_id,
        "cursor_start_date_time": cursor_start_date_time
        }
    
    start_time = time.perf_counter()


    data = get_event_list_from_query(query, parameters)

    end_time = time.perf_counter()
    elapsed_time_ms = (end_time - start_time) * 1000  # convert to milliseconds

    print("took ", str(elapsed_time_ms), " milliseconds for host future")
    
    elapsed_time_ms = (start_time - begin_start_time) * 1000  # convert to milliseconds

    print("took ", str(elapsed_time_ms), " milliseconds before calling query to get host future") 

    return data


@is_requester_privileged_for_user
async def join_past(request: Request) -> JSONResponse:
    user_id = request.path_params["user_id"]

    body = await request.json()
    cursor_event_id = body.get("cursor_event_id", None)
    cursor_start_date_time = body.get("cursor_start_date_time", None)

    try:
        assert all({user_id})
    except:
        Response(status_code=400, content="Incomplete body")

    cursor_clause = ""
    if cursor_event_id and cursor_start_date_time:
        cursor_clause = "AND (e.StartDateTime < datetime($cursor_start_date_time) OR (e.StartDateTime = datetime($cursor_start_date_time) AND e.EventID < $cursor_event_id))"

    query = f"""MATCH ((e:Event)-[:user_join]-(u:User{{UserID:$user_id}})), ((host:User)-[:user_host]->(e))
                WITH DISTINCT e,
                    COUNT{{ (e)<-[:user_join]-() }} as num_joins,
                    COUNT{{ (e)<-[:user_shoutout]-() }} as num_shoutouts,
                    exists((u)-[:user_join]->(e)) as user_join,
                    exists((u)-[:user_shoutout]->(e)) as user_shoutout,
                    host.UserID as host_user_id
                WHERE e.StartDateTime < datetime() {cursor_clause}
                RETURN {{ event_id: e.EventID,
                        title: e.Title,
                        picture: e.Picture,
                        description: e.Description,
                        location: e.Location,
                        start_date_time: e.StartDateTime,
                        end_date_time: e.EndDateTime,
                        visibility: e.Visibility,
                        num_joins: num_joins,
                        num_shoutouts: num_shoutouts,
                        user_join: user_join,
                        user_shoutout: user_shoutout,
                        host_user_id: host_user_id }} as event
                ORDER BY e.StartDateTime DESC, e.EventID DESC
                LIMIT 20
                """

    parameters={
        "user_id": user_id,
        "cursor_event_id": cursor_event_id,
        "cursor_start_date_time": cursor_start_date_time
        }

    return get_event_list_from_query(query, parameters) 

 
@is_requester_privileged_for_user
async def join_future(request: Request) -> JSONResponse:
    user_id = request.path_params["user_id"]

    body = await request.json()
    cursor_event_id = body.get("cursor_event_id", None)
    cursor_start_date_time = body.get("cursor_start_date_time", None)

    cursor_clause = ""
    if cursor_event_id and cursor_start_date_time:
        cursor_clause = "AND (e.StartDateTime > datetime($cursor_start_date_time) OR (e.StartDateTime = datetime($cursor_start_date_time) AND e.EventID > $cursor_event_id))"

    query = f"""MATCH ((e:Event)-[:user_join]-(u:User{{UserID:$user_id}})), ((host:User)-[:user_host]->(e))
                WITH DISTINCT e,
                    COUNT{{(e)<-[:user_join]-() }} as num_joins,
                    COUNT{{ (e)<-[:user_shoutout]-() }} as num_shoutouts,
                    exists((u)-[:user_join]->(e)) as user_join,
                    exists((u)-[:user_shoutout]->(e)) as user_shoutout,
                    host.UserID as host_user_id
                WHERE e.StartDateTime >= datetime() {cursor_clause}
                RETURN {{ event_id: e.EventID,
                        title: e.Title,
                        picture: e.Picture,
                        description: e.Description,
                        location: e.Location,
                        start_date_time: e.StartDateTime,
                        end_date_time: e.EndDateTime,
                        visibility: e.Visibility,
                        num_joins: num_joins,
                        num_shoutouts: num_shoutouts,
                        user_join: user_join,
                        user_shoutout: user_shoutout,
                        host_user_id: host_user_id }} as event
                ORDER BY e.StartDateTime ASC, e.EventID ASC
                LIMIT 20
                """

    parameters={
        "user_id": user_id,
        "cursor_event_id": cursor_event_id,
        "cursor_start_date_time": cursor_start_date_time
        }

    return get_event_list_from_query(query, parameters) 


async def get_home_events(request: Request) -> JSONResponse:

    """
    Request of body type:

        user_access_token

    Path params:
        school_id
    """

    
    school_id = request.path_params["school_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")

    try:
        assert all((user_access_token, school_id, user_access_token))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body or incorrect parameter")

    with get_neo4j_session() as session:
        result = session.run(
            """
            MATCH (e:Event)-[:user_host]-(host:User)
            WHERE e.StartDateTime > datetime() AND e.StartDateTime <= datetime() + duration({days: 30})
            AND (host)<-[:user_follow]-(:User{UserAccessToken: $user_access_token}) 
            AND NOT (e)<-[:user_host]-(:User{UserAccessToken: $user_access_token}) 
            AND NOT (e)<-[:user_join]-(:User{UserAccessToken: $user_access_token})
            AND NOT (e)<-[:user_not_interested]-(:User{UserAccessToken: $user_access_token})
            AND (e)-[:event_school]-(:School{SchoolID: $school_id})
            WITH e, host, COUNT{(e)<-[:user_join]-()} as num_joins, exists((:User{UserAccessToken: $user_access_token})-[:user_follow]->(host)) as user_follow_host,  COUNT{(e)<-[:user_shoutout]-()} as num_shoutouts, exists((:User{UserAccessToken: $user_access_token})-[:user_join]->(e)) as user_join, exists((:User{UserAccessToken: $user_access_token})-[:user_shoutout]->(e)) as user_shoutout
            ORDER BY RAND()
            LIMIT 25
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
                reason: "From an account you follow",
                user_follow_host: user_follow_host
                }) AS event_data
            UNWIND event_data as results
            RETURN results

            UNION

            MATCH (e:Event)-[:user_host]-(host:User)
            WHERE e.StartDateTime > datetime() AND e.StartDateTime <= datetime() + duration({days: 14})
            AND NOT (e)<-[:user_host]-(:User{UserAccessToken: $user_access_token}) 
            AND NOT (e)<-[:user_join]-(:User{UserAccessToken: $user_access_token})
            AND NOT (e)<-[:user_not_interested]-(:User{UserAccessToken: $user_access_token})
            AND (e)-[:event_school]-(:School{SchoolID: $school_id})
            WITH e, host, COUNT{(e)<-[:user_join]-()} as num_joins, exists((:User{UserAccessToken: $user_access_token})-[:user_follow]->(host)) as user_follow_host, COUNT{(e)<-[:user_shoutout]-()} as num_shoutouts, exists((:User{UserAccessToken: $user_access_token})-[:user_join]->(e)) as user_join, exists((:User{UserAccessToken: $user_access_token})-[:user_shoutout]->(e)) as user_shoutout
            ORDER BY RAND()
            LIMIT 10
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
                user_follow_host: user_follow_host
                }) AS event_data
            UNWIND event_data as results
            RETURN results

            UNION

            MATCH (e:Event)-[:user_host]-(host:User)
            WHERE e.StartDateTime > datetime() AND e.StartDateTime <= datetime() + duration({days: 7})
            AND NOT (e)<-[:user_host]-(:User{UserAccessToken: $user_access_token}) 
            AND NOT (e)<-[:user_join]-(:User{UserAccessToken: $user_access_token})
            AND NOT (e)<-[:user_not_interested]-(:User{UserAccessToken: $user_access_token})
            AND (e)-[:event_school]-(:School{SchoolID: $school_id})
            AND host.ScraperAccount IS NOT NULL AND host.ScraperAccount = True
            WITH e, host, COUNT{(e)<-[:user_join]-()} as num_joins, exists((:User{UserAccessToken: $user_access_token})-[:user_follow]->(host)) as user_follow_host, COUNT{(e)<-[:user_shoutout]-()} as num_shoutouts, exists((:User{UserAccessToken: $user_access_token})-[:user_join]->(e)) as user_join, exists((:User{UserAccessToken: $user_access_token})-[:user_shoutout]->(e)) as user_shoutout
            ORDER BY RAND()
            LIMIT 10
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
                user_follow_host: user_follow_host
                }) AS event_data
            UNWIND event_data as results
            RETURN results

            UNION

            MATCH (e:Event)-[:user_host]-(host:User)
            WHERE e.StartDateTime > datetime() AND e.StartDateTime <= datetime() + duration({days: 14})
            AND host.VerifiedOrganization = true 
            AND NOT (e)<-[:user_host]-(:User{UserAccessToken: $user_access_token}) 
            AND NOT (e)<-[:user_join]-(:User{UserAccessToken: $user_access_token})
            AND NOT (e)<-[:user_not_interested]-(:User{UserAccessToken: $user_access_token})
            AND (e)-[:event_school]-(:School{SchoolID: $school_id})
            WITH e, host, exists((:User{UserAccessToken: $user_access_token})-[:user_follow]->(host)) as user_follow_host, COUNT{(e)<-[:user_join]-()} as num_joins, COUNT{(e)<-[:user_shoutout]-()} as num_shoutouts, exists((:User{UserAccessToken: $user_access_token})-[:user_join]->(e)) as user_join, exists((:User{UserAccessToken: $user_access_token})-[:user_shoutout]->(e)) as user_shoutout
            ORDER BY RAND()
            LIMIT 10
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
                reason: "From a reputable organization",
                user_follow_host: user_follow_host
            }) AS event_data
            UNWIND event_data as results
            RETURN results

            UNION

            MATCH (e:Event)-[:user_host]-(host:User)
            WHERE e.StartDateTime > datetime() AND e.StartDateTime <= datetime() + duration({days: 21})
            AND NOT (e)<-[:user_join]-(:User{UserAccessToken: $user_access_token})
            AND NOT (e)<-[:user_host]-(:User{UserAccessToken: $user_access_token})
            AND NOT (e)<-[:user_not_interested]-(:User{UserAccessToken: $user_access_token})
            AND (e)-[:event_school]-(:School{SchoolID: $school_id})
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
                user_follow_host: user_follow_host
                }) AS popular_events
            UNWIND apoc.coll.shuffle(popular_events)[0..15] AS results
            RETURN results""",
            parameters={
                "user_access_token": user_access_token,
                "school_id": school_id,
            }
        )

        data = []
        event_id_list = {}

        for record in result:
            row = record["results"]

            user_id = row["user_id"]
            display_name = row["display_name"]
            username = row["username"]
            host_picture = row["host_picture"]
            verified_organization = row.get("verified_organization", False)

            event_id = row['event_id']
            if(event_id_list.get(event_id)):
                continue
            event_id_list[event_id] = True
            title = row['title']
            event_picture = row['event_picture']
            description = row['description']
            location = row['location']
            start_date_time = str(row['start_date_time'])
            end_date_time = None if row["end_date_time"] == "NULL" else str(row["end_date_time"])
            visibility = row['visibility']
            num_joins = row["num_joins"]
            num_shoutouts = row["num_shoutouts"]
            user_join = row['user_join']
            user_shoutout = row['user_shoutout']
            host_user_id = row['host_user_id']
            user_follow_host = row['user_follow_host']
            reason = row.get("reason")

            data.append({
                "host": {
                    "user_id": user_id,
                    "display_name": display_name,
                    "username": username,
                    "picture": host_picture,
                    "verified_organization": verified_organization,
                },
                "event": {
                    'event_id': event_id,
                    'title': title,
                    'picture': event_picture,
                    'description': description,
                    'location': location,
                    'start_date_time': start_date_time,
                    'end_date_time': end_date_time,
                    'visibility': visibility,
                    'num_joins': num_joins,
                    'num_shoutouts': num_shoutouts,
                    'user_join': user_join,
                    'user_shoutout': user_shoutout,
                    'host_user_id': host_user_id,
                    'user_follow_host': user_follow_host
                },
                "reason": reason
            })
        
        random.shuffle(data)
        return JSONResponse(data)
    
@is_requester_privileged_for_user
@is_requester_privileged_for_event    
async def post_event_message(request: Request) -> JSONResponse:

    """
    parameters: {
        user_access_token: string,
        message: string,
        ping_joined_users: boolean,
    }
    """

    user_id = request.path_params.get("user_id")
    event_id = request.path_params.get("event_id")
    
    request.state.background = BackgroundTasks()

    request_data = await parse_request_data(request)

    user_access_token = request_data.get("user_access_token")
    message = request_data.get("message")
    ping_joined_users = request_data.get("ping_joined_users")

    try:
        assert all((user_id, event_id, user_access_token))
        assert type(ping_joined_users) == bool
    except AssertionError:
        return Response(status_code=400, content="Incomplete body or incorrect parameter")
    
    if(len(message) > 3000):
        return Response(status_code=400, content="Message is beyond 3000 characters. Please shorten it")
    
    document_id = create_firestore_event_message(event_id, user_id, message)

    if(ping_joined_users):
        user = get_user_entity_by_user_id(user_id, None, False)
        try:
            joined_users_push_tokens_with_user_id = get_all_joined_users_push_tokens(event_id)
            if(joined_users_push_tokens_with_user_id is not None):
                request.state.background.add_task(
                        send_and_validate_expo_push_notifications, 
                        joined_users_push_tokens_with_user_id, "New event message", str(user['username']) + ": " + str(message), {
                        'action': 'ViewEventDetailsMessages',
                        'event_id': event_id,
                    })
        except Exception as e:
            print("ERROR SENDING FOLLOWER PUSH NOTIFICATION: \n\n" + str(e))

    return JSONResponse({
        'message_id': document_id
    })

@is_requester_privileged_for_user 
@is_requester_privileged_for_event    
async def delete_event_message(request: Request) -> JSONResponse:

    """
    parameters: {
        user_access_token: string,
        message_id: string,
    }
    """

    user_id = request.path_params.get("user_id")
    event_id = request.path_params.get("event_id")

    request_data = await parse_request_data(request)

    user_access_token = request_data.get("user_access_token")
    message_id = request_data.get("message_id")

    try:
        assert all((user_id, event_id, user_access_token, message_id))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body or incorrect parameter")
    
    delete_firestore_event_message(event_id, message_id)
    return Response(content="Message deleted")

routes = [
    Route("/event/create_event",
        create_event,
        methods=["POST"],
    ),
    Route("/event/event_id/{event_id}", get_event, methods=["POST"]),
    Route("/event/event_id/{event_id}", update_event, methods=["UPDATE"]),
    Route("/event/event_id/{event_id}", delete_event, methods=["DELETE"]),
    Route("/event/school_id/{school_id}/categorized",
        get_events_categorized,
        methods=["POST"],
    ),
    Route("/event/user_id/{user_id}/host_past",
        host_past,
        methods=["POST"],
    ),
    Route("/event/user_id/{user_id}/host_future",
        host_future,
        methods=["POST"],
    ),
    Route("/event/user_id/{user_id}/join_past",
        join_past,
        methods=["POST"],
    ),
    Route("/event/user_id/{user_id}/join_future",
        join_future,
        methods=["POST"],
    ),
    Route("/event/school_id/{school_id}/search",
        search_events,
        methods=["POST"],
    ),
    Route("/event/school_id/{school_id}/home",
        get_home_events,
        methods=["POST"],
    ),
    # Route("/event/event_id/{event_id}/user_id/{user_id}/post_message",
    #     post_event_message,
    #     methods=["POST"],
    # ),
    # Route("/event/event_id/{event_id}/user_id/{user_id}/delete_message",
    #     delete_event_message,
    #     methods=["POST"],
    # )
]


# HELPER FUNCTIONS

def get_event_list_from_query(query, parameters):

    with get_neo4j_session() as session:
        # check if email exists
        result = session.run(
            query,
            parameters   
        )

        events = []
        for record in result:
            event_data = record['event']
            event_id = event_data['event_id']
            title = event_data['title']
            picture = event_data['picture']
            description = event_data['description']
            location = event_data['location']
            start_date_time = str(event_data['start_date_time'])
            end_date_time = None if event_data["end_date_time"] == "NULL" else str(event_data["end_date_time"])
            visibility = event_data['visibility']
            num_joins = event_data['num_joins']
            num_shoutouts = event_data['num_shoutouts']
            user_join = event_data['user_join']
            user_shoutout = event_data['user_shoutout']
            host_user_id = event_data['host_user_id']

            events.append({
                'event_id': event_id,
                'title': title,
                'picture': picture,
                'description': description,
                'location': location,
                'start_date_time': start_date_time,
                'end_date_time': end_date_time,
                'visibility': visibility,
                'num_joins': num_joins,
                'num_shoutouts': num_shoutouts,
                'user_join': user_join,
                'user_shoutout': user_shoutout,
                'host_user_id': host_user_id
            })
            
        return JSONResponse(events)

