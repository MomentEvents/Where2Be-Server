from inspect import Parameter

from markupsafe import string
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.routing import Route

from fastapi_utils.timing import record_timing

from datetime import datetime
import bcrypt
import secrets

from cloud_resources.moment_neo4j import get_connection
from version.ver_1_0_0.auth import is_real_user

import platform
from version.ver_1_0_0.auth import is_requester_privileged_for_user,is_event_formatted


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

    with get_connection() as session:
        # check if email exists
        result = session.run(
            """MATCH (s:School) 
            RETURN s
            ORDER BY toLower(s.Abbreviation + s.Name)""",
        )

        record_timing(request, note="request time")

        school_array = []
        for record in result:

            if record == None:
                return Response(status_code=400, content="Schools do not exist")

            data = record[0]
            school_array.append(
                {
                    "school_id": data["SchoolID"],
                    "name": data["Name"],
                    "abbreviation": data["Abbreviation"],
                }
            )

        return JSONResponse(school_array)


async def get_school(request: Request) -> JSONResponse:
    """
    Description: Gets a user {user_id}’s school.

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

    with get_connection() as session:
        # check if email exists
        result = session.run(
            """match (u:School{SchoolID : $school_id}) return u""",
            parameters={
                "school_id": school_id,
            },
        )

        record_timing(request, note="request time")

        # get the first element of object
        record = result.single()

        if record == None:
            return Response(status_code=400, content="School does not exist")

        data = record[0]

        school_data = {
            "school_id": data["SchoolID"],
            "name": data["DisplayName"],
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

    with get_connection() as session:
        # check if email exists
        result = session.run(
            """match (u:User{UserID : $user_id})-[:user_school]->(s:School) return s""",
            parameters={
                "user_id": user_id,
            },
        )

        record_timing(request, note="request time")

        # get the first element of object
        record = result.single()

        if record == None:
            return Response(status_code=400, content="User does not exist")

        data = record[0]

        school_data = {
            "school_id": data["SchoolID"],
            "name": data["DisplayName"],
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

    with get_connection() as session:
        # check if email exists
        result = session.run(
            """match (u:User{UserID : $user_id})-[:user_school]->(s:School {SchoolID: $school_id}) return s""",
            parameters={"user_id": user_id, "school_id": school_id},
        )

        record_timing(request, note="request time")

        # get the first element of object
        record = result.single()

        # if
        if record != None:
            return Response(status_code=200, content="Connection already exists")
        else:
            result = session.run(
                """match (u:User{UserID : $user_id})-[r:user_school]->(prev_s), (s:School {SchoolID: $school_id}) 
                delete r
                create (u)-[:user_school]->(s)""",
                parameters={"user_id": user_id, "school_id": school_id},
            )

            return Response(status_code=200, content="Connection created exists")


routes = [
    Route(
        "/api_ver_1.0.0/school",
        get_all_schools,
        methods=["GET"],
    ),
    Route(
        "/api_ver_1.0.0/school/school_id/{school_id}",
        get_school,
        methods=["GET"],
    ),
    Route(
        "/api_ver_1.0.0/school/user_id/{user_id}",
        get_user_school,
        methods=["GET"],
    ),
    Route(
        "/api_ver_1.0.0/school/user_id/{user_id}",
        update_user_school,
        methods=["UPDATE"],
    ),
]
