from inspect import Parameter

from markupsafe import string
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from fastapi_utils.timing import record_timing

# from datetime import datetime
from dateutil import parser
import bcrypt
import secrets

from cloud_resources.moment_neo4j import get_connection
from version.ver_1_0_0.auth import is_real_user, is_requester_privileged_for_event, is_requester_privileged_for_user,is_event_formatted, is_real_event, is_picture_formatted, error_handler, is_valid_user_access_token
from helpers import parse_request_data

from cloud_resources.moment_s3 import upload_base64_image


import platform

from io import BytesIO
import io

import boto3

import base64
from PIL import Image
import json
import cv2
import numpy as np

@error_handler
@is_valid_user_access_token
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


    return:
        event_id: string

    """

    request_data = await parse_request_data(request)

    user_access_token = request_data.get("user_access_token")
    title = request_data.get("title")
    description = request_data.get("description")
    location = request_data.get("location")
    start_date_time = parser.parse(request_data.get("start_date_time"))
    end_date_time = None if request_data.get("end_date_time") is None else parser.parse(request_data.get("end_date_time"))
    visibility = request_data.get("visibility")
    interest_ids = [*set(json.loads(request_data.get("interest_ids")))]
    picture = request_data.get("picture")

    event_id = secrets.token_urlsafe()
    image_id = secrets.token_urlsafe()
    event_image = await upload_base64_image(picture, "app-uploads/images/events/event-id/"+event_id+"/", image_id)

    with get_connection() as session:
        # check if email exists
        result = session.run(
            """MATCH (user:User {UserAccessToken: $user_access_token})-[:user_school]->(school:School)
                CREATE (event:Event {
                    EventID: $event_id,
                    Title: $title,
                    Description: $description,
                    Picture: $image,
                    Location: $location,
                    StartDateTime: $start_date_time,
                    EndDateTime: $end_date_time,
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
        record_timing(request, note="request time")

    event_data = {
        "event_id": str(event_id),
    }

    return JSONResponse(event_data)

@error_handler
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
    with get_connection() as session:

        # check if email exists
        result = session.run(
                """MATCH (event:Event{EventID : $event_id}), (user:User{UserAccessToken:$user_access_token}) 
                WITH (event),
                    size ((event)<-[:user_join]-()) as num_joins,
                    size ((event)<-[:user_shoutout]-()) as num_shoutouts,
                    exists ((event)<-[:user_join]-(user)) as user_join,
                    exists ((event)<-[:user_shoutout]-(user)) as user_shoutout
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
                    user_shoutout: user_shoutout
                }""",
            parameters={
                "event_id": event_id,
                "user_access_token": user_access_token,
            },
        )

        record_timing(request, note="request time")

        # get the first element of object
        record = result.single()

        if record == None:
            return Response(status_code=400, content="Event does not exist")

        data = record[0]

        print("Testing\n\n\n\n")
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
        }

        return JSONResponse(event_data)

@error_handler
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

    with get_connection() as session:
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

@error_handler
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

    return:

    """
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

    print(event_id)

    event_image = None
    if picture != "null" and picture != "undefined":
        image_id = secrets.token_urlsafe()
        event_image = await upload_base64_image(picture, "app-uploads/images/events/event-id/"+event_id+"/", image_id)
    else:
        picture = None

    
    with get_connection() as session:
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
        record_timing(request, note="request time")

    return Response(status_code=200, content="event updated")

@error_handler
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

    with get_connection() as session:

        if user_access_token == None:
            result = session.run(
                """
                MATCH (e:Event)-[:event_school]->(school:School {SchoolID: $school_id})
                WITH DISTINCT e,
                    size( (e)<-[:user_join]-() ) as num_joins,
                    size( (e)<-[:user_shoutout]-() ) as num_shoutouts
                WHERE e.StartDateTime >= datetime()
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
                        user_shoutout: False 
                    } as event
                ORDER BY num_joins+num_shoutouts DESC
                LIMIT 3
                WITH collect(event) as events
                RETURN apoc.map.setKey({}, "Featured", events) as event_dict

                UNION

                MATCH (e:Event)-[:event_school]->(school:School {SchoolID: $school_id})
                WITH DISTINCT e, 
                    size( (e)<-[:user_join]-() ) as num_joins,
                    size( (e)<-[:user_shoutout]-() ) as num_shoutouts
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
                        user_shoutout: False 
                    } as event
                ORDER BY num_joins+num_shoutouts DESC
                LIMIT 20
                WITH collect(event) as events
                RETURN apoc.map.setKey({}, "Ongoing", events) as event_dict

                UNION
                
                MATCH (e:Event)-[:event_school]->(school:School {SchoolID: $school_id}), (e)-[:event_tag]->(i:Interest)
                WITH DISTINCT e, i,
                    size( (e)<-[:user_join]-() ) as num_joins,
                    size( (e)<-[:user_shoutout]-() ) as num_shoutouts
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
                        user_shoutout: False 
                    } as event
                ORDER BY e.StartDateTime
                WITH interest, collect(event) as events
                RETURN apoc.map.setKey({}, interest, events) as event_dict
                """,
                # """MATCH (e:Event)-[:event_school]->(school:School {SchoolID: $school_id})
                # WITH DISTINCT e, 
                #     size( (e)<-[:user_join]-() ) as num_joins,
                #     size( (e)<-[:user_shoutout]-() ) as num_shoutouts
                # WHERE e.StartDateTime >= datetime()
                # WITH
                #     { 
                #         event_id: e.EventID,
                #         title: e.Title,
                #         picture: e.Picture,
                #         description: e.Description,
                #         location: e.Location,
                #         start_date_time: e.StartDateTime,
                #         end_date_time: e.EndDateTime,
                #         visibility: e.Visibility,
                #         num_joins: num_joins,
                #         num_shoutouts: num_shoutouts,
                #         user_join: False,
                #         user_shoutout: False 
                #     } as event
                # ORDER BY num_joins+num_shoutouts DESC
                # LIMIT 3
                # WITH collect(event) as events
                # RETURN apoc.map.setKey({}, "Featured", events) as event_dict

                # UNION

                # MATCH (e:Event)-[:event_school]->(school:School {SchoolID: $school_id})
                # WITH DISTINCT e, 
                #     size( (e)<-[:user_join]-() ) as num_joins,
                #     size( (e)<-[:user_shoutout]-() ) as num_shoutouts
                # WHERE (datetime() < e.EndDateTime) AND (datetime() > e.StartDateTime)
                # WITH
                #     { 
                #         event_id: e.EventID,
                #         title: e.Title,
                #         picture: e.Picture,
                #         description: e.Description,
                #         location: e.Location,
                #         start_date_time: e.StartDateTime,
                #         end_date_time: e.EndDateTime,
                #         visibility: e.Visibility,
                #         num_joins: num_joins,
                #         num_shoutouts: num_shoutouts,
                #         user_join: False,
                #         user_shoutout: False 
                #     } as event
                # ORDER BY num_joins+num_shoutouts DESC
                # LIMIT 3
                # WITH collect(event) as events
                # RETURN apoc.map.setKey({}, "Ongoing", events) as event_dict

                # UNION
                
                # MATCH (e:Event)-[:event_school]->(school:School {SchoolID: $school_id}), (e)-[:event_tag]->(i:Interest)
                # ORDER BY i.Name
                # WITH DISTINCT e, i,
                #     size( (e)<-[:user_join]-() ) as num_joins,
                #     size( (e)<-[:user_shoutout]-() ) as num_shoutouts
                # WHERE e.StartDateTime >= datetime()
                # WITH i.DisplayName as interest,
                #     { 
                #         event_id: e.EventID,
                #         title: e.Title,
                #         picture: e.Picture,
                #         description: e.Description,
                #         location: e.Location,
                #         start_date_time: e.StartDateTime,
                #         end_date_time: e.EndDateTime,
                #         visibility: e.Visibility,
                #         num_joins: num_joins,
                #         num_shoutouts: num_shoutouts,
                #         user_join: False,
                #         user_shoutout: False 
                #     } as event
                # ORDER BY e.StartDateTime
                # WITH interest, collect(event) as events
                # LIMIT 20
                # RETURN apoc.map.setKey({}, interest, events) as event_dict
                # """,
                parameters={
                    "school_id": school_id,
                },
            )
            record_timing(request, note="request time")
        else:
            result = session.run(
                """
                MATCH (e:Event)-[:event_school]->(school:School {SchoolID: $school_id}),(u:User{UserAccessToken: $user_access_token})
                WITH DISTINCT e,
                    size( (e)<-[:user_join]-() ) as num_joins,
                    size( (e)<-[:user_shoutout]-() ) as num_shoutouts,
                    exists((u)-[:user_join]->(e)) as user_join,
                    exists((u)-[:user_shoutout]->(e)) as user_shoutout
                WHERE e.StartDateTime >= datetime()
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
                        user_shoutout: user_shoutout 
                    } as event
                ORDER BY num_joins+num_shoutouts DESC
                LIMIT 3
                WITH collect(event) as events
                RETURN apoc.map.setKey({}, "Featured", events) as event_dict

                UNION

                MATCH (e:Event)-[:event_school]->(school:School {SchoolID: $school_id}),(u:User{UserAccessToken: $user_access_token})
                WITH DISTINCT e, 
                    size( (e)<-[:user_join]-() ) as num_joins,
                    size( (e)<-[:user_shoutout]-() ) as num_shoutouts,
                    exists((u)-[:user_join]->(e)) as user_join,
                    exists((u)-[:user_shoutout]->(e)) as user_shoutout
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
                        user_shoutout: user_shoutout 
                    } as event
                ORDER BY num_joins+num_shoutouts DESC
                LIMIT 20
                WITH collect(event) as events
                RETURN apoc.map.setKey({}, "Ongoing", events) as event_dict

                UNION
                
                MATCH (e:Event)-[:event_school]->(school:School {SchoolID: $school_id}), (e)-[:event_tag]->(i:Interest),(u:User{UserAccessToken: $user_access_token})
                WITH DISTINCT e, i,
                    size( (e)<-[:user_join]-() ) as num_joins,
                    size( (e)<-[:user_shoutout]-() ) as num_shoutouts,
                    exists((u)-[:user_join]->(e)) as user_join,
                    exists((u)-[:user_shoutout]->(e)) as user_shoutout
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
                        user_shoutout: user_shoutout 
                    } as event
                ORDER BY e.StartDateTime
                WITH interest, collect(event) as events
                RETURN apoc.map.setKey({}, interest, events) as event_dict
                """,
                parameters={
                    "school_id": school_id,
                    "user_access_token": user_access_token
                },
            )
            record_timing(request, note="request time")

        categorized_dict = {}
        event_ids = []
        for record in result:
            # print("record1: ",record)
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
                            'user_shoutout': user_shoutout
                        })

                if events!= []:
                    categorized_dict[interest] = events

        return JSONResponse(categorized_dict)

@error_handler
async def get_events(request: Request) -> JSONResponse:
    """
    Description: Gets all events attached to a school of {school_id} 

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

    try:
        assert all({user_access_token, school_id})
    except:
        Response(status_code=400, content="Incomplete body")

    with get_connection() as session:
        # check if email exists
        result = session.run(
                """MATCH (e:Event)-[:event_school]->(school: School{SchoolID: $school_id}), (u:User{UserAccessToken:$user_access_token})
            WITH DISTINCT e,
                size( (e)<-[:user_join]-() ) as num_joins,
                size( (e)<-[:user_shoutout]-() ) as num_shoutouts,    
                exists((u)-[:user_join]->(e)) as user_join,
                exists((u)-[:user_shoutout]->(e)) as user_shoutout
            WHERE e.StartDateTime >= datetime() - duration({hours: 12})
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
                    user_shoutout: user_shoutout } as event
            ORDER BY toLower(e.Title)
            """,
            parameters={
                "school_id": school_id,
                "user_access_token": user_access_token,
            },
        )
        record_timing(request, note="request time")

        events = []
        for record in result:
            event_data = record['event']
            event_id = event_data['event_id']
            title = event_data['title']
            picture = event_data['picture']
            description = event_data['description']
            location = event_data['location']
            start_date_time = str(event_data['start_date_time'])
            end_date_time = None if event_data["end_date_time"] == "NULL" else str(event_data["end_date_time"]),
            visibility = event_data['visibility']
            num_joins = event_data['num_joins']
            num_shoutouts = event_data['num_shoutouts']
            user_join = event_data['user_join']
            user_shoutout = event_data['user_shoutout']

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
                'user_shoutout': user_shoutout
            })

        return JSONResponse(events)

@error_handler
async def host_past(request: Request) -> JSONResponse:
    """
    Description: Gets the past hosted events attached to a user of {user_id}. Limits to 20 events. Orders from closest start time all the way until further out.
    params:

    return:
    Array of… {
        event_id: string,
        title: string,
        description: string,
        location: string,
        start_date_time: Date(?),
        end_date_time: Date(?),
        visibility: boolean

    """
    user_id = request.path_params["user_id"]

    body = await request.json()
    user_access_token = body["user_access_token"]

    try:
        assert all({user_access_token, user_id})
    except:
        Response(status_code=400, content="Incomplete body")

    query = """MATCH ((e:Event)-[:user_host]-(u:User{UserID:$user_id})), (c:User{UserAccessToken: $user_access_token})
                WITH DISTINCT e,
                    size( (e)<-[:user_join]-() ) as num_joins,
                    size( (e)<-[:user_shoutout]-() ) as num_shoutouts,
                    exists((c)-[:user_join]->(e)) as user_join,
                    exists((c)-[:user_shoutout]->(e)) as user_shoutout
                WHERE e.StartDateTime < datetime()
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
                        user_shoutout: user_shoutout } as event
                ORDER BY e.StartDateTime DESC
                LIMIT 20
                """

    parameters={
        "user_id": user_id,
        "user_access_token": user_access_token
        }

    return get_event_list_from_query(query, parameters)    

@error_handler
async def host_future(request: Request) -> JSONResponse:
    """
    Description: Gets the future hosted events attached to a user of {user_id}. Limits to 20 events. Orders from closest start time all the way until further out.

    params:
        user_access_token

    return:
    Array of… {
        event_id: string,
        title: string,
        description: string,
        location: string,
        start_date_time: Date(?),
        end_date_time: Date(?),
        visibility: boolean

    """
    
    user_id = request.path_params["user_id"]

    body = await request.json()
    user_access_token = body["user_access_token"]

    try:
        assert all({user_access_token, user_id})
    except:
        Response(status_code=400, content="Incomplete body")

    query = """MATCH ((e:Event)-[:user_host]-(u:User{UserID:$user_id})), (c:User{UserAccessToken: $user_access_token})
                WITH DISTINCT e,
                    size( (e)<-[:user_join]-() ) as num_joins,
                    size( (e)<-[:user_shoutout]-() ) as num_shoutouts,
                    exists((c)-[:user_join]->(e)) as user_join,
                    exists((c)-[:user_shoutout]->(e)) as user_shoutout
                WHERE e.StartDateTime >= datetime()
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
                        user_shoutout: user_shoutout } as event
                ORDER BY e.StartDateTime
                LIMIT 20
                """

    parameters={
        "user_id": user_id,
        "user_access_token": user_access_token
        }

    return get_event_list_from_query(query, parameters)

@error_handler
@is_requester_privileged_for_user
async def join_past(request: Request) -> JSONResponse:
    """
    Description: Gets the past joined events attached to a user of {user_id}. Limits to 20 events. Orders from closest start time all the way until further out.

    params:

    return:
    Array of… {
        event_id: string,
        title: string,
        description: string,
        location: string,
        start_date_time: Date(?),
        end_date_time: Date(?),
        visibility: boolean

    """
    user_id = request.path_params["user_id"]

    try:
        assert all({user_id})
    except:
        Response(status_code=400, content="Incomplete body")


    query = """MATCH ((e:Event)-[:user_join]-(u:User{UserID:$user_id}))
                WITH DISTINCT e,
                    size( (e)<-[:user_join]-() ) as num_joins,
                    size( (e)<-[:user_shoutout]-() ) as num_shoutouts,
                    exists((u)-[:user_join]->(e)) as user_join,
                    exists((u)-[:user_shoutout]->(e)) as user_shoutout
                WHERE e.StartDateTime < datetime()
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
                        user_shoutout: user_shoutout } as event
                ORDER BY e.StartDateTime DESC
                LIMIT 20
                """

    parameters={
        "user_id": user_id
        }

    return get_event_list_from_query(query, parameters) 

@error_handler
@is_requester_privileged_for_user
async def join_future(request: Request) -> JSONResponse:
    """
    Description: Gets the future joined events attached to a user of {user_id}. Limits to 20 events. Orders from closest start time all the way until further out.

    params:

    return:
    Array of… {
        event_id: string,
        title: string,
        description: string,
        location: string,
        start_date_time: Date(?),
        end_date_time: Date(?),
        visibility: boolean

    """
    user_id = request.path_params["user_id"]

    query = """MATCH ((e:Event)-[:user_join]-(u:User{UserID:$user_id}))
                WITH DISTINCT e,
                    size( (e)<-[:user_join]-() ) as num_joins,
                    size( (e)<-[:user_shoutout]-() ) as num_shoutouts,
                    exists((u)-[:user_join]->(e)) as user_join,
                    exists((u)-[:user_shoutout]->(e)) as user_shoutout
                WHERE e.StartDateTime >= datetime()
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
                        user_shoutout: user_shoutout } as event
                ORDER BY e.StartDateTime
                LIMIT 20
                """

    parameters={
        "user_id": user_id
        }

    return get_event_list_from_query(query, parameters) 

routes = [
    Route(
        "/api_ver_1.0.0/event/create_event",
        create_event,
        methods=["POST"],
    ),
    Route("/api_ver_1.0.0/event/event_id/{event_id}", get_event, methods=["POST"]),
    Route("/api_ver_1.0.0/event/event_id/{event_id}", update_event, methods=["UPDATE"]),
    Route("/api_ver_1.0.0/event/event_id/{event_id}", delete_event, methods=["DELETE"]),
    Route(
        "/api_ver_1.0.0/event/school_id/{school_id}/categorized",
        get_events_categorized,
        methods=["POST"],
    ),
     Route(
        "/api_ver_1.0.0/event/school_id/{school_id}",
        get_events,
        methods=["POST"],
    ),
    Route(
        "/api_ver_1.0.0/event/user_id/{user_id}/host_past",
        host_past,
        methods=["POST"],
    ),
    Route(
        "/api_ver_1.0.0/event/user_id/{user_id}/host_future",
        host_future,
        methods=["POST"],
    ),
    Route(
        "/api_ver_1.0.0/event/user_id/{user_id}/join_past",
        join_past,
        methods=["POST"],
    ),
    Route(
        "/api_ver_1.0.0/event/user_id/{user_id}/join_future",
        join_future,
        methods=["POST"],
    ),
]


# HELPER FUNCTIONS

def get_event_list_from_query(query, parameters):

    with get_connection() as session:
        # check if email exists
        result = session.run(
            query,
            parameters   
        )
        # record_timing(request, note="request time")

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
                'user_shoutout': user_shoutout
            })
            
        return JSONResponse(events)

