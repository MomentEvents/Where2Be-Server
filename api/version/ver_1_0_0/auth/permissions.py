from functools import wraps
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from api.cloud_resources.moment_neo4j import get_connection

admin_user_access_tokens = {"ogzccTkpufyNJI_8uUxus1YJHnDVo6lKPdEaa5dZqJQ",
}

def is_real_user(func):
    @wraps(func)
    async def wrapper(request: Request) -> JSONResponse:

        request_data = await parse_request_data(request)

        if request_data is None:
            return Response(status_code=400, content="Request is in invalid format")

        user_access_token = request_data["user_access_token"]

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
                return Response(status_code=401, content="User does not exist")

            return await func(request)

    return wrapper

def is_real_event(func):
    @wraps(func)
    async def wrapper(request: Request) -> JSONResponse:

        request_data = await parse_request_data(request)

        if request_data is None:
            return Response(status_code=400, content="Request is in invalid format")

        event_id = request_data["event_id"]

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

def is_picture_real(func):
    @wraps(func)
    async def wrapper(request: Request) -> JSONResponse:

        request_data = await parse_request_data(request)

        if request_data is None:
            return Response(status_code=400, content="Request is in invalid format")

        picture = request_data["picture"]
        
        try:
            assert all((picture))
        except AssertionError:
            return Response(status_code=400, content="Invalid picture")

        return await func(request)

    return wrapper

def is_event_formatted(func):
    @wraps(func)
    async def wrapper(request: Request) -> JSONResponse:

        request_data = await parse_request_data(request)

        if request_data is None:
            return Response(status_code=400, content="Request is in invalid format")

        title = request_data["title"]
        description = request_data["description"]
        location = request_data["location"]
        start_date_time = request_data["start_date_time"]
        end_date_time = request_data["end_date_time"]
        visibility = request_data["visibility"]
        interest_ids = request_data["interest_ids"]
        interest_ids = json.loads(interest_ids)
        
        try:
            assert all((title,
            description, 
            location,
            start_date_time,
            end_date_time,
            visibility,
            interest_ids
            ))
        except AssertionError:
            return Response(status_code=400, content="Body is incomplete")


        
        
        return await func(request)

    return wrapper

def is_user_formatted(func):
    @wraps(func)
    async def wrapper(request: Request) -> JSONResponse:

        content_type = request.headers.get("Content-Type")
        semicolon_index = content_type.find(";")

        if semicolon_index != -1:
            content_type = content_type[:semicolon_index]

        event_id = None

        if content_type == "application/json":
            event_id = request.path_params["event_id"]

        elif content_type == "multipart/form-data":
            event_id = request.path_params["event_id"]

        else:
            return Response(status_code=400, content="Request is in neither proper format")

        try:
            assert all((event_id))
        except AssertionError:
            return Response(status_code=400, content="Incomplete body")

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

def is_user_privileged_for_user(func):
    @wraps(func)
    async def wrapper(request: Request) -> JSONResponse:

        user_access_token = None
        user_id = None

        content_type = request.headers.get("Content-Type")
        semicolon_index = content_type.find(";")

        if semicolon_index != -1:
            content_type = content_type[:semicolon_index]

        if content_type == "application/json":
            user_id = request.path_params["user_id"]
            json_data = await request.json()
            user_access_token = json_data["user_access_token"]

        elif content_type == "multipart/form-data":
            user_id = request.path_params["user_id"]
            form_data = await request.form()
            user_access_token = form_data["user_access_token"]

        else:
            print(type(content_type))
            return Response(status_code=400, content="Request in neither proper format")

        try:
            assert all((user_access_token, user_id))
        except AssertionError:
            return Response(status_code=400, content="Incomplete body")

        if is_user_privileged(user_access_token):
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

def is_user_privileged_for_event(func):
    @wraps(func)
    async def wrapper(request: Request) -> JSONResponse:

        user_access_token = None
        event_id = None

        content_type = request.headers.get("Content-Type")
        semicolon_index = content_type.find(";")

        if semicolon_index != -1:
            content_type = content_type[:semicolon_index]

        if content_type == "application/json":
            event_id = request.path_params["event_id"]
            json_data = await request.json()
            user_access_token = json_data["user_access_token"]

        elif content_type == "multipart/form-data":
            event_id = request.path_params["event_id"]
            form_data = await request.form()
            user_access_token = form_data["user_access_token"]

        else:
            return Response(status_code=400, content="Request is not in proper format")

        try:
            assert all((user_access_token, event_id))
        except AssertionError:
            return Response(status_code=400, content="Incomplete body")

        if is_user_privileged(user_access_token):
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

################################## helper functions

def is_user_privileged(user_access_token) -> bool:
    
    return user_access_token in admin_user_access_tokens

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

