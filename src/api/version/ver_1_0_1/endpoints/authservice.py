from inspect import Parameter
from common.models import Problem
from common.neo4j.commands.schoolcommands import get_school_entity_by_school_id
from common.neo4j.commands.usercommands import create_user_entity, get_user_entity_by_username
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.routing import Route


from api.version.ver_1_0_1.auth import is_requester_admin, is_user_formatted
from api.helpers import parse_request_data

import datetime
import bcrypt
import secrets

from common.neo4j.moment_neo4j import get_neo4j_session
from common.s3.moment_s3 import get_bucket_url
from common.commands import login, signup
from common.firebase import send_password_reset_email, send_verification_email

from common.constants import SCRAPER_TOKEN
 
async def login_user(request: Request) -> JSONResponse:
    """
    Description: Send a username and password and returns a user_access_token attached to the associated user object

    params:
        username: string,
        password: string,

    return:
        string user_access_token

    """

    body = await request.json()
    usercred = body.get("usercred")
    password = body.get("password")

    try:
        assert all({usercred, password})
    except:
        return Response(status_code=400, content="Incomplete body")

    usercred = usercred.lower()

    usercred = usercred.strip()

    user_id, user_access_token = login(usercred, password)
    print("user_id returned to API: ", user_id)
    print("user_access_token returned to API: ", user_access_token)

    return JSONResponse({"user_id": user_id, "user_access_token": user_access_token})


 
@is_user_formatted
async def signup_user(request: Request) -> JSONResponse:
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
    email = body.get("email")

    try:
        assert all((username, password, display_name, school_id, email))
    except AssertionError:
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Invalid request in body")

    user_access_token = signup(username, display_name, email, password, school_id)

    print("CREATED USER")
    print(user_access_token)

    return Response(status_code=200, content="User created")


async def verify_email(request: Request) -> JSONResponse:
    """
    Description: Changes the password for an account.

    params:
        email: string

    return:

    """

    request_data = await parse_request_data(request)

    email = request_data.get("email")

    try:
        assert all((email))
    except AssertionError:
        # Handle the error here
        return Response(status_code=400, content="Invalid request in body")

    email = email.strip()
    send_verification_email(email)

    return Response(status_code=200, content="Sent verification email")

 
async def reset_password(request: Request) -> JSONResponse:
    """
    Description: Changes the password for an account.

    params:
        email: string

    return:

    """

    request_data = await parse_request_data(request)

    email = request_data.get("email")

    try:
        assert all((email))
    except AssertionError:
        # Handle the error here
        return Response(status_code=400, content="Invalid request in body")

    email = email.strip()
    send_password_reset_email(email)

    return Response(status_code=200, content="Sent password reset email")


async def check_if_user_is_admin(request: Request) -> JSONResponse:

    body = await request.json()

    user_access_token = body.get("user_access_token")
    try:
        assert ({user_access_token})
    except:
        return Response(status_code=400, content="User access token is blank")
    
    return JSONResponse({"is_admin": is_requester_admin(user_access_token)})

@is_user_formatted
async def create_user_without_verify(request: Request) -> JSONResponse:
    body = await request.json()

    username = body.get("username")
    password = body.get("password")
    display_name = body.get("display_name")
    school_id = body.get("school_id")
    scraper_token = body.get("scraper_token")

    try:
        assert all((username, password, display_name, school_id, scraper_token))
    except AssertionError:
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Invalid request in body")

    if(scraper_token != SCRAPER_TOKEN):
        raise Problem(status=401, content="Invalid scraper token")

    username = username.lower()
    username = username.strip()
    display_name = display_name.strip()

    school = get_school_entity_by_school_id(school_id)

    if(school is None):
        raise Problem(status=400, content="School does not exist")
    
    user = get_user_entity_by_username(username)

    if(user is not None):
        raise Problem(status=400, content="Username already exists")
    
    user_access_token, user_id = create_user_entity(display_name, username, school_id, False, False)

    return JSONResponse({"user_access_token": user_access_token, "user_id": user_id})




routes = [
    Route("/auth/login",
        login_user,
        methods=["POST"],
    ),
    Route("/auth/signup", signup_user, methods=["POST"]),
    Route("/auth/verify_email", verify_email, methods=["POST"]),
    Route("/auth/reset_password",
          reset_password, methods=["POST"]),
    Route("/auth/privileged_admin",
          check_if_user_is_admin, methods=["POST"]),
    Route("/auth/create_scraper_account",
          create_user_without_verify, methods=["POST"]),
]
