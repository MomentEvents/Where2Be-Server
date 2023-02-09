from inspect import Parameter
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.routing import Route

from fastapi_utils.timing import record_timing

from api.version.ver_1_0_0.auth import is_user_privileged, parse_request_data, error_handler, is_user_formatted

import datetime
import bcrypt
import secrets

from api.cloud_resources.moment_neo4j import get_connection
from api.cloud_resources.moment_s3 import get_bucket_url
import random

@error_handler
async def get_status(request: Request) -> JSONResponse:
    request_data = await parse_request_data(request)
    print(request_data.get("app_version"))
    return Response(status_code=200)
    # return Response(content="This version of Moment is not supported. Update to the latest version.", status_code=400)

@error_handler
async def get_token_username(request: Request) -> JSONResponse:
    """
    Description: Send a username and password and returns a user_access_token attached to the associated user object

    params:
        username: string,
        password: string,

    return:
        string user_access_token

    """
    # username = request.query_params.get("username")
    # password = request.query_params.get("password")

    body = await request.json()
    username = body.get("username")
    password = body.get("password")

    # Connect to the database and run a simple query
    with get_connection() as session:
        result = session.run(
            """MATCH (u:User) 
            WHERE u.Username = $username 
            RETURN u""",
            parameters={"username": username},
        )

        record_timing(request, note="request time")

        # get the first element of object
        record = result.single()

        if record == None:
            return Response(status_code=400, content="Username does not exist")

        data = record[0]

        print(password)

        if not bcrypt.checkpw(password.encode("utf-8"), data.get("PasswordHash")):
            return Response(status_code=401, content="Password Incorrect")

        user_access_token = {
            "user_access_token": data.get("UserAccessToken"),
        }

        return JSONResponse(user_access_token)

@error_handler
@is_user_formatted
async def create_user(request: Request) -> JSONResponse:
    """
    Description: Sends the information and creates a new user. Returns a user_access_token attached to the associated user object.

    params:
        username: string,
        display_name: string,
        email: string,
        password: string,
        school_id: string

    return:
        user_access_token: string,

    """

    body = await request.json()

    username = body.get("username")
    password = body.get("password")
    display_name = body.get("display_name")
    school_id = body.get("school_id")

    try:
        assert all((username, password, display_name, school_id))
    except AssertionError:
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Invalid request in body")

    # input checks
    username = username.lower()

    

    email_exists = False
    username_exists = False

    random_number = str(random.randint(1, 5))
    default_user_image = (
        get_bucket_url()+"app-uploads/images/users/static/default" + random_number + ".png"
    )

    with get_connection() as session:

        # check if username exists
        result = session.run(
            "MATCH (u:User {Username: $username}) RETURN u",
            parameters={"username": username},
        )
        record_timing(request, note="request username time")
        record = result.single()
        if record != None:
            username_exists = True

        # if email_exists and username_exists:
        #     return Response(status_code=400, content="Username and Email already exist")
        # elif username_exists:
        #     return Response(status_code=400, content="Username already exists")
        # elif email_exists:
        #     return Response(status_code=400, content="Email already exists")

        if username_exists:
            return Response(status_code=400, content="Username already exists")

        hashed_password = get_hash_pwd(password)
        user_access_token = secrets.token_urlsafe()

        result = session.run(
            """Create (u:User {UserID: $username, Username: $username, Picture:$picture, Name:$display_name, PasswordHash:$hashed_password, UserAccessToken:$user_access_token})
            With u
            Match(n:School{SchoolID: $school_id})
            create (u)-[r:user_school]->(n)
            Return u""",
            parameters={
                "username": username,
                "display_name": display_name,
                "picture": default_user_image,
                "hashed_password": hashed_password,
                "school_id": school_id,
                "user_access_token": user_access_token,
            },
        )

        return JSONResponse({"user_access_token": user_access_token})

@error_handler
async def check_if_user_is_admin(request: Request) -> JSONResponse:
    
    body = await request.json()

    user_access_token = body.get("user_access_token")
    try:
        assert({user_access_token})
    except:
        return Response(status_code=400, content="User access token is blank")

    return JSONResponse({"is_admin": is_user_privileged(user_access_token)})

routes = [
    Route(
        "/api_ver_1.0.0/auth/login/username",
        get_token_username,
        methods=["POST"],
    ),
    Route(
        "/api_ver_1.0.0/status",
        get_status,
        methods=["POST"]
    ),
    Route("/api_ver_1.0.0/auth/signup", create_user, methods=["POST"]),
    Route("/api_ver_1.0.0/auth/privileged_admin", check_if_user_is_admin, methods=["POST"]),
]

# HELPER FUNCTIONS 

def get_hash_pwd(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())