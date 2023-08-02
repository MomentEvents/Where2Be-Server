from inspect import Parameter

from markupsafe import string
from common.neo4j.commands.schoolcommands import get_all_school_entities, get_school_entity_by_user_id
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.routing import Route

import time


from datetime import datetime
import bcrypt
import secrets

from common.neo4j.moment_neo4j import parse_neo4j_data, run_neo4j_query
from api.version.ver_1_0_1.auth import is_real_user

import platform
from api.version.ver_1_0_1.auth import is_requester_privileged_for_user, is_event_formatted


if platform.system() == "Windows":
    from asyncio.windows_events import NULL


 
async def get_all_schools(request: Request) -> JSONResponse:
    """
    Description: Gets all of the schools within the database

    params:

    return :
        return: Array of… {
                        school_id: string,
                        name: string,
                        abbreviation: string
                }

    """

    start_time = time.perf_counter()

    school_array = await get_all_school_entities()

    end_time = time.perf_counter()

    elapsed_time_ms = (end_time - start_time) * 1000  # convert to milliseconds

    print("took ", str(elapsed_time_ms), " milliseconds to get all schools") 


    return JSONResponse(school_array)


 
async def get_school(request: Request) -> JSONResponse:
    """
    Description: Gets a school's information.

    params:

    return :
        return: Array of… {
                        school_id: string,
                        name: string,
                        abbreviation: string
                }

    """

    school_id = request.path_params["school_id"]

    try:
        assert all((school_id))
    except AssertionError:
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Parameter Missing")

    # check if email exists
    result = await run_neo4j_query(
        """match (u:School{SchoolID : $school_id}) return u""",
        parameters={
            "school_id": school_id,
        },
    )

    data = parse_neo4j_data(result, 'single')

    if(data is None):
        return None

    school_data = {
        "school_id": data["SchoolID"],
        "name": data["Name"],
        "abbreviation": data["Abbreviation"],
        "latitude": data["Latitude"],
        "longitude": data["Longitude"],
    }

    return JSONResponse(school_data)


 
async def get_user_school(request: Request) -> JSONResponse:
    """
    Description: Gets a user {user_id}’s school.

    params:

    return :
        school_id: string,
        name: string,
        abbreviation: string,

    """

    user_id = request.path_params["user_id"]

    try:
        assert all((user_id))
    except AssertionError:
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Parameter Missing")
    
    school_data = await get_school_entity_by_user_id(user_id)

    return JSONResponse(school_data)


 
async def get_user_access_token_school(request: Request) -> JSONResponse:

    user_access_token = request.path_params["user_access_token"]

    try:
        assert all((user_access_token))
    except AssertionError:
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Parameter Missing")

    result = await run_neo4j_query(
        """match (u:User{UserAccessToken : $user_access_token})-[:user_school]->(s:School) return s""",
        parameters={
            "user_access_token": user_access_token,
        },
    )

    data = parse_neo4j_data(result, 'single')

    if(data is None):
        return None

    school_data = {
        "school_id": data["SchoolID"],
        "name": data["Name"],
        "abbreviation": data["Abbreviation"],
        "latitude": data["Latitude"],
        "longitude": data["Longitude"],
    }

    return JSONResponse(school_data)


 
@is_requester_privileged_for_user
async def update_user_school(request: Request) -> JSONResponse:
    """
    Description: Updates a user {user_id}’s school to school_id.

    params:
        user_access_token: string,
        school_id: string


    return :
        school_id: string,
        name: string,
        abbreviation: string,

    """

    user_id = request.path_params["user_id"]

    body = await request.json()

    school_id = body.get("school_id")

    try:
        assert all((user_id))
    except AssertionError:
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Parameter Missing")

    # check if email exists
    result = await run_neo4j_query(
        """match (u:User{UserID : $user_id})-[:user_school]->(s:School {SchoolID: $school_id}) return s""",
        parameters={"user_id": user_id, "school_id": school_id},
    )

    if result != None:
        return Response(status_code=200, content="Connection already exists")
    else:
        result = await run_neo4j_query(
            """match (u:User{UserID : $user_id})-[r:user_school]->(prev_s), (s:School {SchoolID: $school_id}) 
            delete r
            create (u)-[:user_school]->(s)""",
            parameters={"user_id": user_id, "school_id": school_id},
        )

        return Response(status_code=200, content="Connection created exists")


routes = [
    Route("/school",
        get_all_schools,
        methods=["GET"],
    ),
    Route("/school/user_access_token/{user_access_token}",
        get_user_access_token_school,
        methods=["GET"],
    ),
    Route("/school/school_id/{school_id}",
        get_school,
        methods=["GET"],
    ),
    Route("/school/user_id/{user_id}",
        get_user_school,
        methods=["GET"],
    ),
    # Route("/school/user_id/{user_id}",
    #     update_user_school,
    #     methods=["UPDATE"],
    # ),
]
