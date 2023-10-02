from inspect import Parameter

from markupsafe import string
from common.models import Problem
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

from common.neo4j.converters import convert_user_entity_to_user, convert_event_entity_to_event


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

    print(data)

    if(data is None):
        raise Problem(status=404, content="User does not exist")

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


async def search_school_events_and_users(request: Request) -> JSONResponse:

    """
    Description: Gets all of the events and users associated with a school of $school_id
    params:
        user_access_token: string

    return:

        [
        user_id: string,
        display_name: string,
        username: string,
        picture: string,
        verified_organization: boolean,
        ]

    """

    school_id = request.path_params["school_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")
    query = body.get("query")

    try:
        assert all((user_access_token, school_id, query))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body")

    query = query.strip()

    result = await run_neo4j_query(
        """ MATCH (s:School{SchoolID: $school_id})
        CALL {

        WITH s
        MATCH (s) <- [:user_school] - (u:User)
        WITH u, toLower(u.DisplayName) as name
        WHERE (toLower(u.DisplayName) CONTAINS toLower($query) OR toLower(u.Username) CONTAINS toLower($query))
        RETURN u as data, name

        UNION

        WITH s
        MATCH (s)<-[:event_school]-(e:Event)
        MATCH (e)<-[:user_host]-(host:User)
        MATCH (u:User{UserAccessToken: $user_access_token})
        WITH DISTINCT e,
            COUNT{(e)<-[:user_join]-()} as num_joins,
            COUNT{(e)<-[:user_shoutout]-()} as num_shoutouts,
            exists((u)-[:user_join]->(e)) as user_join,
            exists((u)-[:user_shoutout]->(e)) as user_shoutout,
            host.UserID as host_user_id,
            toLower(e.Title) as name
        WHERE e.StartDateTime >= datetime() AND (toLower(e.Title) CONTAINS toLower($query) OR toLower(e.Location) CONTAINS toLower($query))
        RETURN {
                EventID: e.EventID,
                Title: e.Title,
                Picture: e.Picture,
                Description: e.Description,
                Location: e.Location,
                StartDateTime: e.StartDateTime,
                EndDateTime: e.EndDateTime,
                Visibility: e.Visibility,
                SignupLink: e.SignupLink,
                num_joins: num_joins,
                num_shoutouts: num_shoutouts,
                user_join: user_join,
                user_shoutout: user_shoutout,
                host_user_id: host_user_id
                } as data, name
        }
        RETURN data
        ORDER BY name
        LIMIT 20
        """,
        parameters={
            "school_id": school_id,
            "query": query,
            "user_access_token": user_access_token,
        },
    )

    users_and_events = []

    for record in result:
        data = record['data']
        if 'UserID' in data:
            users_and_events.append(convert_user_entity_to_user(data=data, show_num_events_followers_following=False))
        elif 'EventID' in record['data']:
            users_and_events.append(convert_event_entity_to_event(data))

    return JSONResponse(
        users_and_events
    )

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
    Route("/school/school_id/{school_id}/search",
        search_school_events_and_users,
        methods=["POST"],
    ),
    # Route("/school/user_id/{user_id}",
    #     update_user_school,
    #     methods=["UPDATE"],
    # ),
]
