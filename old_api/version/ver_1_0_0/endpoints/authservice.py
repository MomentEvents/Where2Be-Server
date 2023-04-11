from inspect import Parameter
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.routing import Route

from fastapi_utils.timing import record_timing

from version.ver_1_0_0.auth import is_requester_privileged, error_handler, is_user_formatted
from helpers import parse_request_data

import datetime
import bcrypt
import secrets

from cloud_resources.moment_neo4j import get_neo4j_session
from cloud_resources.moment_s3 import get_bucket_url
import random


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

    body = await request.json()
    username = body.get("username")
    password = body.get("password")

    try:
        assert all({username, password})
    except:
        return Response(status_code=400, content="Incomplete body")

    username = username.lower()

    # Connect to the database and run a simple query
    with get_neo4j_session() as session:
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
            return Response(status_code=401, content="Incorrect password")

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
    username = username.strip()
    display_name = display_name.strip()

    if len(password) < 7:
        return Response(status_code=400, content="Please enter a more complex password")

    if len(password) > 30:
        return Response(status_code=400, content="Your password is over 30 characters. Please enter a shorter password")

    email_exists = False
    username_exists = False

    random_number = str(random.randint(1, 5))
    default_user_image = (
        get_bucket_url()+"app-uploads/images/users/static/default" + random_number + ".png"
    )

    with get_neo4j_session() as session:

        # check if username exists
        result = session.run(
            "MATCH (u:User {Username: $username}) RETURN u",
            parameters={"username": username},
        )
        record_timing(request, note="request username time")
        record = result.single()
        if record != None:
            username_exists = True

        if username_exists:
            return Response(status_code=400, content="Username already exists")

        hashed_password = get_hash_pwd(password)
        user_access_token = secrets.token_urlsafe()
        user_id = secrets.token_urlsafe()

        # check if school exists

        result = session.run(
            """
            MATCH(s:School{SchoolID: $school_id})
            RETURN s""",
            parameters={
                "school_id": school_id,
            },
        )
        record = result.single()

        if record == None:
            return Response(status_code=400, content="School does not exist")

        result = session.run(
            """CREATE (u:User {UserID: $user_id, Username: $username, Picture:$picture, DisplayName:$display_name, PasswordHash:$hashed_password, UserAccessToken:$user_access_token})
            WITH u
            MATCH(n:School{SchoolID: $school_id})
            CREATE (u)-[r:user_school]->(n)
            RETURN u""",
            parameters={
                "username": username,
                "display_name": display_name,
                "picture": default_user_image,
                "hashed_password": hashed_password,
                "school_id": school_id,
                "user_access_token": user_access_token,
                "user_id": user_id,
            },
        )

        return JSONResponse({"user_access_token": user_access_token})


@error_handler
async def change_password(request: Request) -> JSONResponse:
    """
    Description: Changes the password for an account.

    params:
        user_access_token: string,
        old_password: string,
        new_password: string,

    return:

    """

    request_data = await parse_request_data(request)

    user_access_token = request_data.get("user_access_token")
    old_password = request_data.get("old_password")
    new_password = request_data.get("new_password")

    try:
        assert all((user_access_token, old_password, new_password))
    except AssertionError:
        # Handle the error here
        return Response(status_code=400, content="Invalid request in body")

    if len(new_password) < 7:
        return Response(status_code=400, content="Please enter a more complex new password")

    if len(new_password) > 30:
        return Response(status_code=400, content="Your new password is over 30 characters. Please enter a shorter password")

    with get_neo4j_session() as session:
        result = session.run(
            """MATCH (u:User {UserAccessToken: $user_access_token}) 
            RETURN u""",
            parameters={
                "user_access_token": user_access_token,
            },
        )

        record = result.single()

        if record == None:
            return Response(status_code=400, content="User does not exist")

        data = record[0]

        if not bcrypt.checkpw(old_password.encode("utf-8"), data.get("PasswordHash")):
            return Response(status_code=401, content="Old password does not match")

        new_password = get_hash_pwd(new_password)
        result = session.run(
            """MATCH (u:User {UserAccessToken: $user_access_token}) 
            SET u.PasswordHash = $new_password
            RETURN u""",
            parameters={
                "user_access_token": user_access_token,
                "new_password": new_password,
            },
        )

        return Response(status_code=200, content="Changed password")


@error_handler
async def check_if_user_is_admin(request: Request) -> JSONResponse:

    body = await request.json()

    user_access_token = body.get("user_access_token")
    try:
        assert ({user_access_token})
    except:
        return Response(status_code=400, content="User access token is blank")

    return JSONResponse({"is_admin": is_requester_privileged(user_access_token)})

routes = [
    Route(
        "/api_ver_1.0.0/auth/login/username",
        get_token_username,
        methods=["POST"],
    ),
    Route("/api_ver_1.0.0/auth/signup", create_user, methods=["POST"]),
    Route("/api_ver_1.0.0/auth/change_password",
          change_password, methods=["POST"]),
    Route("/api_ver_1.0.0/auth/privileged_admin",
          check_if_user_is_admin, methods=["POST"]),
]

# HELPER FUNCTIONS


def get_hash_pwd(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
