from datetime import datetime, timezone
from common.utils import is_event_formatted_correctly, is_picture_formatted_correctly, is_user_formatted_correctly
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from functools import wraps
from dateutil import parser
from common.neo4j.moment_neo4j import parse_neo4j_data, run_neo4j_query
from api.helpers import parse_request_data
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

        is_valid, message = is_picture_formatted_correctly(picture)
        if(not is_valid):
            return Response(status=400, content=message)
        
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

        is_valid, message = await is_event_formatted_correctly(title, description, start_date_time,
                                                               end_date_time, location, visibility, interest_ids)
        if(not is_valid):
            return Response(status=400, content=message)

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

        is_valid, message = is_user_formatted_correctly(display_name, username)

        if(not is_valid):
            return Response(status=400, content=message)

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

        if(data is None):
            return Response(status_code=401, content="Unauthenticated")


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

        data = parse_neo4j_data(result, "multiple")
        if data == None:
            return Response(status_code=401, content="Unauthorized")
        

        print("The requester privileged event wrapper result is ", data)
        if(data["did_host"] or (data['u'].get("Administrator", False))):
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
