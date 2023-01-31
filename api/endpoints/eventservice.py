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

from api.neo4j_init import get_connection
from api.auth import check_user_access_token


import platform

from io import BytesIO

if platform.system() == "Windows":
    from asyncio.windows_events import NULL

import boto3

s3 = boto3.client('s3', aws_access_key_id='AKIAR6GV237CVGO4R54X',
    aws_secret_access_key='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')

access_key = 'AKIAR6GV237CVGO4R54X' #'AKIA2IIOOLB6IZ4NQOWM'
secret_access_key = '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' #'YuCZO2+yId3Hj4yBwUXkuIxUiP12100pIH6V6TyW'  #change when putting in py file

# Creating Session With Boto3.
session = boto3.Session(
aws_access_key_id=access_key,
aws_secret_access_key=secret_access_key
)

#Creating S3 Resource From the Session.
s3 = session.resource('s3')

upload_file_bucket =  'moment-events' #test-bucket-chirag5241' #moment-events.s3.us-east-2


# error handling for broken queries!
# event_data = {
#     "event_id": event_id,
#     # "title": title,
#     # "description": description,
#     # "location": location,
#     # "start_date_time": start_date_time,
#     # "end_date_time": end_date_time,
#     # "visibility": visibility,
#     # "interest_ids": interest_ids,
# }

# return JSONResponse(event_data)


def get_hash_pwd(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def event_query(query, parameters):

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
            end_date_time = str(event_data["end_date_time"]) if event_data["end_date_time"] != "NULL" else None
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


# @check_user_access_token
async def create_event(request: Request) -> JSONResponse:
    """
    Description: Creates an event associated with the user in the user_access_token. Returns an error if too many events are created at the same time from that same user (for spam)

    params:
        user_access_token: string,
        title: string,
        description: string,
        location: string,
        start_date_time: Date(?),
        end_date_time: Date(?),
        visibility: boolean,
        interest_id: string[]


    return:
        event_id: string

    """

    form_data = await request.form()

    user_access_token = form_data["user_access_token"]
    title = form_data["title"]
    description = form_data["description"]
    location = form_data["location"]
    start_date_time = form_data["start_date_time"]
    end_date_time = form_data["end_date_time"]
    visibility = form_data["visibility"]
    interest_ids = form_data["interest_ids"]
    picture = form_data["picture"]

    file_data = await picture.read()

    print("############user_access_token",picture)

    


    # with open(picture.filename, 'rb') as f:
    with BytesIO(file_data) as file_obj:
        s3.Object(upload_file_bucket, "test/"+picture.filename).put(Body=file_obj,ContentType='image/PNG')
        # s3.upload_fileobj(file_obj, 'moment-events', "test/"+picture.filename)

    event_data = {
        "event_id": event_id,
        "title": title,
        "description": description,
        "location": location,
        "start_date_time": start_date_time,
        "end_date_time": end_date_time,
        "visibility": visibility,
        "interest_ids": interest_ids,
    }

    return JSONResponse(event_data)

    # body = await request.json()

    # user_access_token = body.get("user_access_token")
    # title = body.get("title")
    # description = body.get("description")
    # location = body.get("location")
    # start_date_time = body.get("start_date_time")
    # end_date_time = body.get("end_date_time")
    # visibility = body.get("visibility")
    # interest_ids = body.get("interest_ids")

    try:
        assert all(
            (
                user_access_token,
                title,
                description,
                location,
                start_date_time,
                # end_date_time,
                visibility,
                interest_ids,
            )
        )
    except AssertionError:
        # Handle the error here
        print("Parameter Missing error")
        return Response(status_code=400, content="Parameter Missing")

    EventID = secrets.token_urlsafe()
    default_user_image = (
        "https://test-bucket-chirag5241.s3.us-west-1.amazonaws.com/test_image.jpeg"
    )

    try:
        # return JSONResponse(start_date_time)
        start_date_time = parser.parse(start_date_time)
    except:
        return Response(status_code=400, content="start date error")

    if end_date_time != None:
        try:
            # return JSONResponse(start_date_time)
            end_date_time = parser.parse(end_date_time)
        except:
            return Response(status_code=400, content="end date error")
    else:
        end_date_time = "NULL"

    with get_connection() as session:
        # check if email exists
        result = session.run(
            """MATCH (user:User {UserAccessToken: $user_access_token})-[:user_school]->(school:School)
                CREATE (event:Event {
                    EventID: $EventID,
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
                "EventID": EventID,
                "user_access_token": user_access_token,
                "image": default_user_image,
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
        "event_id": str(EventID),
    }

    return JSONResponse(event_data)


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

        event_data = {
            "event_id": data["event_id"],
            "picture": data["picture"],
            "title": data["title"],
            "description": data["description"],
            "location": data["location"],
            "start_date_time": str(data["start_date_time"]),
            "end_date_time": str(data["end_date_time"])
            if data["end_date_time"] != "NULL"
            else None,
            "visibility": data["visibility"],
            "num_joins": data["num_joins"],
            "num_shoutouts": data["num_shoutouts"],
            "user_join": data["user_join"],
            "user_shoutout": data["user_shoutout"],
            # "interest_ids": data["UserAccessToken"]interest_ids,
        }

        return JSONResponse(event_data)


async def delete_event(request: Request) -> JSONResponse:
    """
    Description: Deletes an event with an event_id of {event_id}. This returns a valid response when the user_access_token is the owner of the event. Error when the user is not the owner of the event

    params:
        user_access_token: string

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

    with get_connection() as session:
        # check if email exists
        result = session.run(
            """OPTIONAL MATCH (e:Event{EventID : $event_id})<-[r:user_host]-(u:User{UserAccessToken : $user_access_token})
            DETACH DELETE e""",
            parameters={
                "user_access_token": user_access_token,
                "event_id": event_id,
            },
        )

    return Response(status_code=200, content="event deleted " + event_id)


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

    body = await request.json()

    user_access_token = body.get("user_access_token")
    title = body.get("title")
    description = body.get("description")
    location = body.get("location")
    start_date_time = body.get("start_date_time")
    end_date_time = body.get("end_date_time")
    visibility = body.get("visibility")
    interest_ids = body.get("interest_ids")

    try:
        assert all(
            (
                user_access_token,
                title,
                description,
                location,
                start_date_time,
                end_date_time,
                visibility,
                interest_ids,
            )
        )
    except AssertionError:
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Parameter Missing")

    with get_connection() as session:
        # check if email exists
        result = session.run(
            """MATCH (e:Event{EventID : $event_id})
            SET 
                e.Title = COALESCE( {$title}, e.Title),
                e.Description = COALESCE({$description}, e.Description)
                e.Picture = COALESCE( {$image}, e.Picture),
                e.Location = COALESCE({$location}, e.Location)
                e.StartDateTime = COALESCE( {$start_date_time}, e.StartDateTime),
                e.EndDateTime = COALESCE({$end_date_time}, e.EndDateTime)
                e.Visibility = COALESCE({$visibility}, e.Visibility)
                e.TimeCreated = datetime()""",
            parameters={
                "title": title,
                "description": description,
                "image": None,
                "location": location,
                "start_date_time": start_date_time,
                "end_date_time": end_date_time,
                "visibility": visibility,
                "interest_ids": interest_ids,
            },
        )
        record_timing(request, note="request time")


async def get_num_joins(request: Request) -> JSONResponse:
    """
    Description: Gets the number of joins for an event.

    params:

    return:
        num_shoutouts: int

    """
    event_id = str(request.path_params["event_id"])

    with get_connection() as session:
        # check if email exists
        result = session.run(
            """MATCH (n:Event {EventID: $event_id}) RETURN size((n)<-[:user_join]-()) as connections""",
            parameters={
                "event_id": event_id,
            },
        )
        record_timing(request, note="request time")

        # get the first element of object
        record = result.single()

        if record:
            connections = record["connections"]
            return JSONResponse(int(connections))
        else:
            return Response(status_code=400, content="Event does not exist")


async def get_num_shoutouts(request: Request) -> JSONResponse:
    """
    Description: Gets the number of joins for an event.

    params:

    return:
        num_shoutouts: int

    """
    event_id = str(request.path_params["event_id"])

    with get_connection() as session:
        # check if email exists
        result = session.run(
            """MATCH (n:Event {EventID: $event_id}) RETURN size((n)<-[:user_shoutout]-()) as connections""",
            parameters={
                "event_id": event_id,
            },
        )
        record_timing(request, note="request time")

        # get the first element of object
        record = result.single()

        if record:
            connections = record["connections"]
            return JSONResponse(int(connections))
        else:
            return Response(status_code=400, content="Event does not exist")


async def get_featured(request: Request) -> JSONResponse:
    """
    Description: Gets the featured events

    params:

    return:
        num_shoutouts: int

    """
    school_id = request.path_params["school_id"]

    with get_connection() as session:
        # check if email exists
        result = session.run(
            """match (e)-[:event_school]->(school: School{SchoolID: $school_id})
            where e.StartDateTime >= datetime()
            return e
            order by e.StartDateTime
            limit 20""",
            parameters={
                "school_id": school_id,
            },
        )
        record_timing(request, note="request time")

        event_array = []
        for record in result:
            data = record[0]
            event_array.append(
                {
                    "EventID": data["EventID"],
                    "Title": data["Title"],
                    "Description": data["Description"],
                    "Location": data["Location"],
                    "Picture": data["Picture"],
                    "StartDateTime": str(data["StartDateTime"]),
                    "EndDateTime": str(data["EndDateTime"]),
                    "Visibility": data["Visibility"],
                }
            )
        return JSONResponse(event_array)

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
    school_id = request.path_params["school_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")

    print("############user_access_token",user_access_token)

    with get_connection() as session:

        if user_access_token == None:
            result = session.run(
                """MATCH (e:Event)-[:event_school]->(school:School {SchoolID: $school_id})
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
                ORDER BY num_joins+num_shoutouts
                LIMIT 3
                WITH collect(event) as events
                return apoc.map.setKey({}, "Featured", events) as event_dict

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
                ORDER BY num_joins+num_shoutouts
                LIMIT 3
                WITH collect(event) as events
                return apoc.map.setKey({}, "Featured", events) as event_dict

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
            print("record1: ",record)
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
                    end_date_time = str(event_data["end_date_time"]) if event_data["end_date_time"] != "NULL" else None
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

    print("############user_access_token",user_access_token)

    with get_connection() as session:
        # check if email exists
        result = session.run(
                """MATCH (e:Event)-[:event_school]->(school: School{SchoolID: $school_id}), (u:User{UserAccessToken:$user_access_token})
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
                    user_join: False,
                    user_shoutout: False } as event
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
            end_date_time = str(event_data["end_date_time"]) if event_data["end_date_time"] != "NULL" else None,
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

async def get_interest_event(request: Request) -> JSONResponse:
    """
    Description: Gets the {interest_id} events attached to a school of {school_id}. Limits to 20 events. Orders from closest start time.

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
        }

    """
    school_id = request.path_params["school_id"]
    interest_id = request.path_params["interest_id"]
    # (inte:Interest {InterestID: "Academic"})-[:school_interest]->(school:School {SchoolID:"univ_UIUC"})

    with get_connection() as session:
        # check if email exists
        result = session.run(
            """match (e:Event)-[:event_school]->(school:School {SchoolID: $school_id}), (e)-[:event_tag]->(inte:Interest {InterestID: $interest_id})
            return e
            order by e.StartDateTime
            limit 20""",
            parameters={
                "school_id": school_id,
                "interest_id": interest_id,
            },
        )
        record_timing(request, note="request time")

        event_array = []
        for record in result:
            data = record[0]
            event_array.append(
                {
                    "EventID": data["EventID"],
                    "Title": data["Title"],
                    "Description": data["Description"],
                    "Location": data["Location"],
                    "Picture": data["Picture"],
                    "StartDateTime": str(data["StartDateTime"]),
                    "EndDateTime": str(data["EndDateTime"]),
                    "Visibility": data["Visibility"],
                }
            )
        return JSONResponse(event_array)

@check_user_access_token
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

    query = """MATCH ((e:Event)-[:user_host]-(u:User{UserID:$user_id}))
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

    return event_query(query, parameters)    

@check_user_access_token
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

    query = """MATCH ((e:Event)-[:user_host]-(u:User{UserID:$user_id}))
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

    return event_query(query, parameters)


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

    return event_query(query, parameters) 


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

    return event_query(query, parameters) 


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
        "/api_ver_1.0.0/event/event_id/{event_id}/num_joins/",
        get_num_joins,
        methods=["GET"],
    ),
    Route(
        "/api_ver_1.0.0/event/event_id/{event_id}/num_shoutouts/",
        get_num_shoutouts,
        methods=["GET"],
    ),
    Route(
        "/api_ver_1.0.0/event/school_id/{school_id}/featured",
        get_featured,
        methods=["GET"],
    ),
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
        "/api_ver_1.0.0/event/school_id/{school_id}/{interest_id}",
        get_interest_event,
        methods=["GET"],
    ),
    # Route(
    #     "api_ver_1.0.0/event/user_id/{user_id}/for_you",
    #     get_interest_event,
    #     methods=["GET"],
    # ),
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
