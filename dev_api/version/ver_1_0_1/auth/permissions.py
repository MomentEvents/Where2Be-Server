from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from functools import wraps
from markupsafe import string
from dateutil import parser
from cloud_resources.moment_neo4j import get_connection
from debug import IS_DEBUG
from helpers import parse_request_data

import json

admin_user_access_tokens = {"ogzccTkpufyNJI_8uUxus1YJHnDVo6lKPdEaa5dZqJQ",
"JWTntbEefCyMWulyfC4mqTIcYPa3m8wjPM3fOTOY7uc",
"NwAcvNpiD8moi0uy4SqpqkizIpZKNwz-j6BqyLkn6lY",
"rAA8AUz-7QRXmcktfjiAWARD-_GoHrpqzbcTrooHY-U",
"Zhz-LH_nkUJQ8pAAVkSdynNC1UFXS_Wk-ddfBhgvEEE"
}

def error_handler(func):
    @wraps(func)
    async def wrapper(request: Request) -> JSONResponse:

        if IS_DEBUG:
            return await func(request)
        
        try:
            return await func(request)
        except:
            return Response(status_code=500, content="Internal server error occurred")

    return wrapper


def is_valid_user_access_token(func):
    @wraps(func)
    async def wrapper(request: Request) -> JSONResponse:

        request_data = await parse_request_data(request)

        if request_data is None:
            return Response(status_code=400, content="Request is in invalid format")

        user_access_token = request_data.get("user_access_token")

        try:
            assert all((user_access_token))
        except AssertionError:
            return Response(status_code=400, content="User access token is blank")

        with get_connection() as session:
            result = session.run(
                """MATCH (u:User{UserAccessToken: $user_access_token}) 
                RETURN u""",
                parameters={
                    "user_access_token": user_access_token
                },
            )
            record = result.single()
            if record == None:
                return Response(status_code=400, content="User does not exist")

            return await func(request)

    return wrapper


def is_real_user(func):
    @wraps(func)
    async def wrapper(request: Request) -> JSONResponse:

        user_id = request.path_params.get("user_id")

        try:
            assert all((user_id))
        except AssertionError:
            return Response(status_code=400, content="Invalid user id")

        with get_connection() as session:
            result = session.run(
                """MATCH (u:User{UserID: $user_id}) 
                RETURN u""",
                parameters={
                    "user_id": user_id
                },
            )
            record = result.single()
            if record == None:
                return Response(status_code=400, content="User does not exist")

            return await func(request)

    return wrapper

def is_real_event(func):
    @wraps(func)
    async def wrapper(request: Request) -> JSONResponse:

        event_id = request.path_params.get("event_id")

        try:
            assert all((event_id))
        except AssertionError:
            return Response(status_code=400, content="Invalid event id")

        with get_connection() as session:
            result = session.run(
                """MATCH (e:Event{EventID: $event_id}) 
                RETURN e""",
                parameters={
                    "event_id": event_id
                },
            )
            record = result.single()
            if record == None:
                return Response(status_code=401, content="Event does not exist")

            return await func(request)

    return wrapper

def is_picture_formatted(func):
    @wraps(func)
    async def wrapper(request: Request) -> JSONResponse:

        request_data = await parse_request_data(request)

        if request_data is None:
            return Response(status_code=400, content="Request is in invalid format")

        picture = request_data.get("picture")
        
        print(picture)
        try:
            assert all((picture))
        except AssertionError:
            return Response(status_code=400, content="Invalid picture")

        if picture == "null" or picture == "undefined":
            return Response(status_code=400, content="Picture cannot be empty")
        
        return await func(request)

    return wrapper

def is_event_formatted(func):
    @wraps(func)
    async def wrapper(request: Request) -> JSONResponse:

        request_data = await parse_request_data(request)

        if request_data is None:
            return Response(status_code=400, content="Request is in invalid format")

        title = request_data.get("title")
        description = request_data.get("description")
        location = request_data.get("location")
        start_date_time = request_data.get("start_date_time")
        end_date_time = request_data.get("end_date_time")
        visibility = request_data.get("visibility")
        interest_ids = request_data.get("interest_ids")
        
        try:
            assert all((title,
            description, 
            location,
            start_date_time,
            visibility,
            interest_ids
            ))
        except AssertionError:
            return Response(status_code=400, content="Body is incomplete")
        
        interest_ids = [*set(json.loads(interest_ids))]

        if (title.isprintable() is False) or (title.isspace() is True):
            return Response(status_code=400, content="Title is not printable")

        if (len(title) > 70):
            return Response(status_code=400, content="Title cannot be over 70 characters")

        if (len(description) > 1500):
            return Response(status_code=400, content="Description cannot be over 1500 characters")

        try:
            start_date_time_test = parser.parse(start_date_time)
        except:
            return Response(status_code=400, content="Could not parse start date")

        if end_date_time != None:
            try:
                end_date_time_test = parser.parse(end_date_time)
                if start_date_time_test > end_date_time_test:
                    return Response(status_code=400, content="Start date cannot be after end date")
            except:
                return Response(status_code=400, content="Could not parse end date")

        if (len(location) > 50):
            return Response(status_code=400, content="Location cannot be over 50 characters")

        if len(interest_ids) != 1:
            return Response(status_code=400, content="Must only put in one interest tag")
        
        with get_connection() as session:

            result = session.run(
                """UNWIND $interest_ids as interest_id
                    MATCH (interests:Interest {InterestID: interest_id})
                    RETURN interests""",
                parameters={
                    "interest_ids": interest_ids,
                },
            )
            
            # this code sucks
            num_interests = 0
            for record in result:
                num_interests = num_interests + 1
            
            if num_interests != len(interest_ids):
                return Response(status_code=400, content="One or more interests do not exist")

        return await func(request)

    return wrapper

def is_user_formatted(func):
    @wraps(func)
    async def wrapper(request: Request) -> JSONResponse:

        request_data = await parse_request_data(request)

        if request_data is None:
            return Response(status_code=400, content="Request is in invalid format")

        display_name = request_data.get("display_name")
        username = request_data.get("username")

        try:
            assert all({display_name, username})
        except:
            return Response(status_code=400, content="Incomplete body")
        
        if len(display_name) > 20:
            return Response(status_code=400, content="Display name cannot exceed 20 characters")

        if (display_name.isprintable() is False) or (display_name.isspace() is True):
            return Response(status_code=400, content="Display name is not readable")

        if len(username) > 30:
            return Response(status_code=400, content="Username cannot exceed 30 characters")

        if username.isalnum() is False:
            return Response(status_code=400, content="Username must be alphanumeric")

        return await func(request)

    return wrapper

def is_requester_privileged_for_user(func):
    @wraps(func)
    async def wrapper(request: Request) -> JSONResponse:

        request_data = await parse_request_data(request)

        if request_data is None:
            return Response(status_code=400, content="Request is in invalid format")

        user_access_token = request_data.get("user_access_token")
        user_id = request.path_params.get("user_id")

        try:
            assert all((user_access_token, user_id))
        except AssertionError:
            return Response(status_code=400, content="Incomplete body")

        if is_requester_privileged(user_access_token):
            return await func(request)
        
        with get_connection() as session:
            result = session.run(
                """MATCH (u:User{UserAccessToken: $user_access_token, UserID: $user_id}) 
                RETURN u""",
                parameters={
                    "user_access_token": user_access_token,
                    "user_id": user_id,
                },
            )
            record = result.single()
            if record == None:
                return Response(status_code=401, content="Unauthorized access")

            return await func(request)
    return wrapper

def is_requester_privileged_for_event(func):
    @wraps(func)
    async def wrapper(request: Request) -> JSONResponse:

        request_data = await parse_request_data(request)

        if request_data is None:
            return Response(status_code=400, content="Request is in invalid format")

        user_access_token = request_data.get("user_access_token")
        event_id = request.path_params.get("event_id")

        try:
            assert all((user_access_token, event_id))
        except AssertionError:
            return Response(status_code=400, content="Incomplete body")

        if is_requester_privileged(user_access_token):
            return await func(request)
        
        with get_connection() as session:
            result = session.run(
                """MATCH ((event:Event{EventID : $event_id})<-[r:user_host]-(user:User{UserAccessToken:$user_access_token}))
                RETURN r""",
                parameters={
                    "user_access_token": user_access_token,
                    "event_id": event_id,
                },
            )
            record = result.single()
            if record == None:
                return Response(status_code=401, content="Unauthorized access")

            return await func(request)
    return wrapper

# HELPER FUNCTIONS

def is_requester_privileged(user_access_token) -> bool:
    
    return user_access_token in admin_user_access_tokens