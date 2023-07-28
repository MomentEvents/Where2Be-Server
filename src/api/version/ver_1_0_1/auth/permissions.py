from datetime import datetime, timezone
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from functools import wraps
from dateutil import parser
from common.neo4j.moment_neo4j import get_neo4j_session, parse_neo4j_data, run_neo4j_query
from api.helpers import parse_request_data, contains_profanity, contains_url, validate_username
import base64
from PIL import Image
import json
from io import BytesIO
import io

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


        result = await run_neo4j_query(
            """MATCH (u:User{UserAccessToken: $user_access_token}) 
            RETURN u""",
            parameters={
                "user_access_token": user_access_token
            },
        )
        if result == None:
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

        result = await run_neo4j_query(
            """MATCH (u:User{UserID: $user_id}) 
            RETURN u""",
            parameters={
                "user_id": user_id
            },
        )

        if result == None:
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

        result = await run_neo4j_query(
            """MATCH (e:Event{EventID: $event_id}) 
            RETURN e""",
            parameters={
                "event_id": event_id
            },
        )
        if result == None:
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
        try:
            assert all((picture))
        except AssertionError:
            return Response(status_code=400, content="Invalid picture")

        if picture == "null" or picture == "undefined":
            return Response(status_code=400, content="Picture cannot be empty")

        try:
            image_bytes = base64.b64decode(picture)
            img = Image.open(io.BytesIO(image_bytes))
        except:
            return Response(status_code=400, content="Picture is not a valid base64 image")

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
        try:

            interest_ids = [*set(json.loads(interest_ids))]

        except:
            return Response(status_code=400, content="Unable to json parse interest_ids")

        title = title.strip()
        location = location.strip()

        if (title.isprintable() is False) or (title.isspace() is True):
            return Response(status_code=400, content="Title is not printable")

        if (len(title) > 70):
            return Response(status_code=400, content="Title cannot be over 70 characters")

        if (len(title) < 1):
            return Response(status_code=400, content="Title cannot be under 1 character")

        if (contains_profanity(title)):
            return Response(status_code=400, content="We detected profanity in your title. Please change it")

        if (contains_url(title)):
            return Response(status_code=400, content="Title cannot contain a url")

        if (description.isspace()):
            return Response(status_code=400, content="Description is not readable")

        if (len(description) > 2000):
            return Response(status_code=400, content="Description cannot be over 2000 characters")

        if (len(description) < 1):
            return Response(status_code=400, content="Description cannot be under 1 character")

        if (contains_profanity(description)):
            return Response(status_code=400, content="We detected profanity in your description. Please change it")

        try:
            start_date_time_test = parser.parse(start_date_time)
        except:
            return Response(status_code=400, content="Could not parse start date")

        if end_date_time != None:
            try:
                end_date_time_test = parser.parse(end_date_time)
                if start_date_time_test >= end_date_time_test:
                    return Response(status_code=400, content="Start date cannot be equal to or after end date")
            except:
                return Response(status_code=400, content="Could not parse end date")
            
        if start_date_time_test < datetime.now(timezone.utc):
            return Response(status_code=400, content="This event cannot be in the past")

        if (location.isprintable() is False) or (location.isspace() is True):
            return Response(status_code=400, content="Location is not printable")

        if (len(location) > 200):
            return Response(status_code=400, content="Location cannot be over 200 characters")

        if (len(location) < 1):
            return Response(status_code=400, content="Location cannot be under 1 character")

        if (contains_profanity(location)):
            return Response(status_code=400, content="We detected profanity in your location. Please change it")

        if len(interest_ids) != 1:
            return Response(status_code=400, content="Must only put in one interest tag")

        if (visibility != "Public" and visibility != "Private"):
            return Response(status_code=400, content="Visibility must be either \"Public\" or \"Private\"")

        result = await run_neo4j_query(
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

        display_name = display_name.strip()
        username = username.strip()

        try:
            assert all({display_name, username})
        except:
            return Response(status_code=400, content="Incomplete body")

        if len(display_name) > 30:
            return Response(status_code=400, content="Display name cannot exceed 30 characters")
        
        if len(display_name) < 3:
            return Response(status_code=400, content="Display name cannot be below 3 characters")

        if (display_name.isprintable() is False) or (display_name.isspace() is True):
            return Response(status_code=400, content="Display name is not readable")

        if (contains_url(display_name)):
            return Response(status_code=400, content="Display name cannot contain a url")

        if (contains_profanity(display_name)):
            return Response(status_code=400, content="We detected profanity in your display name. Please change it")

        if len(username) > 30:
            return Response(status_code=400, content="Username cannot exceed 30 characters")

        if len(username) < 6:
            return Response(status_code=400, content="Username cannot be under 6 characters")

        if validate_username(username) is False:
            return Response(status_code=400, content="Usernames must contain a-z, A-Z, 0-9, underscores, or hyphens")

        if (contains_profanity(username)):
            return Response(status_code=400, content="We detected profanity in your username. Please change it")

        if (contains_url(username)):
            return Response(status_code=400, content="Username cannot contain a url")

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


        result = await run_neo4j_query(
        """MATCH (u:User{UserAccessToken: $user_access_token}) 
        RETURN u""",
        parameters={
            "user_access_token": user_access_token,
        },
    )
        data = parse_neo4j_data(result, 'single')


        if((data["UserID"] == user_id) or data.get("Administrator", False)):
            return await func(request)
        
        
        return Response(status_code=403, content="Forbidden")
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

        result = await run_neo4j_query(
        """MATCH (u:User{UserAccessToken: $user_access_token}), (e:Event{EventID: $event_id})
        RETURN exists((u)-[:user_host]->(e)) as did_host, u""",
        parameters={
            "user_access_token": user_access_token,
            "event_id": event_id,
        },
        )

        print("The requester privileged event wrapper result is ", result)

        if result == None:
            return Response(status_code=401, content="Unauthorized")
        
        if(result["did_host"] or (result["u"].get("Administrator", False))):
            return await func(request)
        
        return Response(status_code=403, content="Forbidden")

    return wrapper

# HELPER FUNCTIONS


async def is_requester_admin(user_access_token) -> bool:

    result = await run_neo4j_query(
        """MATCH (u:User {UserAccessToken: $user_access_token})
            RETURN {
            Administrator: COALESCE(u.Administrator, false)
            } as result""",
            parameters={
                "user_access_token": user_access_token
            },
        )
    
    data = parse_neo4j_data(result, 'single')

    try:
        is_admin = data['Administrator']
        assert type(is_admin) == bool
    except:
        return False
    
    return is_admin
        


async def parse_request_data(request: Request):

    content_type = request.headers.get("Content-Type")
    semicolon_index = content_type.find(";")

    if semicolon_index != -1:
        content_type = content_type[:semicolon_index]

    if content_type == "application/json":
        request_data = await request.json()
        return request_data

    elif content_type == "multipart/form-data":
        request_data = await request.form()
        return request_data
    else:
        return None
