from inspect import Parameter
import platform
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.routing import Route

import datetime
import bcrypt
import secrets

from neo4j_init import get_connection


# error handling for broken queries!


def get_hash_pwd(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


# this is a function to test if the server is connected to the database
async def data_test(request: Request) -> JSONResponse:

    with get_connection() as session:
        result = session.run(
            "match (n:Event) where n.EventID contains $name return (n) limit 25",
            parameters={"name": "disc"},
        )

        event_array = []
        for record in result:
            data = record[0]
            event_array.append(
                {
                    "EventID": data["EventID"],
                    "Title": data["Title"],
                    # "Description": data["Description"],
                    "Picture": data["Picture"],
                    "StartDateTime": str(data["StartDateTime"]),
                }
            )
        return JSONResponse(event_array)


async def get_token_username(request: Request) -> JSONResponse:
    """
    Description: Send a username and password and returns a user_access_token attached to the associated user object

    params:
        username: string,
        password: string,

    return:
        string user_access_token

    """
    # username = request.query_params["username"]
    # password = request.query_params["password"]

    body = await request.json()
    username = body.get("username")
    password = body.get("password")

    # Connect to the database and run a simple query
    with get_connection() as session:
        result = session.run(
            "match (u:User) where u.Username = $username return u",
            parameters={"username": username, "password": password},
        )


        # get the first element of object
        record = result.single()

        if record == None:
            return Response(status_code=400, content="Username does not exist")

        data = record[0]

        if not bcrypt.checkpw(password.encode("utf-8"), data["PasswordHash"]):
            return Response(status_code=401, content="Password Incorrect")

        user_access_token = {
            "user_access_token": data["UserAccessToken"],
        }

        return JSONResponse(user_access_token)


async def get_token_email(request: Request) -> JSONResponse:
    """
    Description: Send an email and password and returns a user_access_token attached to the associated user object

    params:
        email: string,
        password: string,

    return:
        string user_access_token

    """
    body = await request.json()
    email = body.get("email")
    password = body.get("password")

    try:
        assert all((password, email))
    except AssertionError:
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Parameter Missing")

    with get_connection() as session:

        result = session.run(
            "match (u:User {Email: $email}) return u",
            parameters={"email": email},
        )


        # get the first element of object
        record = result.single()

        if record == None:
            return Response(status_code=400, content="Email does not exist")

        data = record[0]

        if not bcrypt.checkpw(password.encode("utf-8"), data["PasswordHash"]):
            return Response(status_code=400, content="Password Incorrect")

        user_access_token = {
            "user_access_token": data["UserAccessToken"],
        }

        token_data = {
            "user_access_token": str(user_access_token),
        }

        return JSONResponse(token_data)


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
    # email = body.get("email")
    school_id = body.get("school_id")

    try:
        assert all((username, password, display_name, school_id))
    except AssertionError:
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Parameter Missing")

    email_exists = False
    username_exists = False
    default_user_image = (
        "https://test-bucket-chirag5241.s3.us-west-1.amazonaws.com/test_image.jpeg"
    )

    with get_connection() as session:
        # # check if email exists
        # result = session.run(
        #     "MATCH (u:User {Email: $email}) RETURN u",
        #     parameters={"email": email},
        # )
        # record = result.single()
        # if record != None:
        #     email_exists = True

        # check if username exists
        result = session.run(
            "MATCH (u:User {Username: $username}) RETURN u",
            parameters={"username": username},
        )
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
        UserAccessToken = secrets.token_urlsafe()

        result = session.run(
            """Create (u:User {UserID: $username, Username: $username, Picture:$picture, Name:$display_name, PasswordHash:$hashed_password, UserAccessToken:$UserAccessToken})
            With u
            Match(n:School{SchoolID: $school_id})
            create (u)-[r:user_school]->(n)
            Return u""",
            parameters={
                "username": username,
                "display_name": display_name,
                "picture": default_user_image,
                # "email": email,
                "hashed_password": hashed_password,
                "school_id": school_id,
                "UserAccessToken": UserAccessToken,
            },
        )

        return JSONResponse({"user_access_token": UserAccessToken})


routes = [
    Route("/data_test", data_test, methods=["GET"]),
    Route(
        "/api_ver_1.0.0/authentication/login/username",
        get_token_username,
        methods=["POST"],
    ),
    Route(
        "/api_ver_1.0.0/authentication/login/email", get_token_email, methods=["POST"]
    ),
    Route("/api_ver_1.0.0/authentication/signup", create_user, methods=["POST"]),
]
