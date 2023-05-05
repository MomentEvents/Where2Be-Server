from inspect import Parameter

from markupsafe import string
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from fastapi_utils.timing import record_timing

from datetime import datetime
import bcrypt
import secrets

from cloud_resources.moment_neo4j import get_neo4j_session
from version.ver_1_0_0.auth import is_real_user, is_requester_privileged_for_user, is_user_formatted, is_valid_user_access_token

import platform

if platform.system() == "Windows":
    from asyncio.windows_events import NULL

import boto3

import base64
from PIL import Image
import json
from cloud_resources.moment_s3 import upload_base64_image


 
async def get_using_user_access_token(request: Request) -> JSONResponse:
    """
    Description: Gets the user information with the associated user_access_token {user_access_token}. Returns error if no results found.

    params:
        user_access_token: string

    return :
        user_id: string,
        display_name: string,
        username: string,
        picture: string,
    """

    user_access_token = request.path_params["user_access_token"]

    try:
        assert all((user_access_token))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body")

    with get_neo4j_session() as session:
        result = session.run(
            """MATCH (u:User{UserAccessToken : $user_access_token})
            RETURN u""",
            parameters={
                "user_access_token": user_access_token,
            },
        )

        record_timing(request, note="request time")

        record = result.single()

        if record == None:
            return Response(status_code=400, content="User does not exist")

        data = record[0]

        user_data = {
            "user_id": data["UserID"],
            "display_name": data["DisplayName"],
            "username": data["Username"],
            "email": data["Email"],
            "picture": data["Picture"],
        }

        return JSONResponse(user_data)


 
async def get_using_user_id(request: Request) -> JSONResponse:
    """
    Description: Gets the user information with the associated user_id {user_id}. Returns error if no results found.

    params:
        user_id: string

    return :
        user_id: string,
        display_name: string,
        username: string,
        picture: string,

    """

    user_id = request.path_params["user_id"]

    try:
        assert all((user_id))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body")

    with get_neo4j_session() as session:
        result = session.run(
            """MATCH (u:User{UserID : $user_id})
            RETURN u""",
            parameters={
                "user_id": user_id,
            },
        )

        record_timing(request, note="get_using_user_id")

        record = result.single()

        if record == None:
            return Response(status_code=400, content="User does not exist")

        data = record[0]

        user_data = {
            "user_id": data["UserID"],
            "display_name": data["DisplayName"],
            "username": data["Username"],
            "picture": data["Picture"],
        }

        return JSONResponse(user_data)


 
@is_user_formatted
@is_requester_privileged_for_user
async def update_using_user_id(request: Request) -> JSONResponse:
    """
    Description: Updates the user information with the associated user_id {user_id}. The {user_id}’s user_access_token needs to match the passed in user_access_token to be able to update the user. Returns error if failed.

    params:
        user_id: string

    return :
        user_id: string,
        display_name: string,
        username: string,
        picture: string,

    """

    user_id = request.path_params["user_id"]

    form_data = await request.form()

    user_access_token = form_data["user_access_token"]
    display_name = form_data["display_name"]
    username = form_data["username"]
    picture = form_data["picture"]

    if picture != "null" and picture != "undefined":
        image_id = secrets.token_urlsafe()
        picture = await upload_base64_image(picture, "app-uploads/images/users/user-id/"+user_id+"/", image_id)
    else:
        picture = None

    username = username.lower()

    username = username.strip()
    display_name = display_name.strip()

    with get_neo4j_session() as session:
        result = session.run(
            """MATCH (u:User{UserID: $user_id}) 
            SET 
                u.DisplayName = COALESCE($display_name, u.DisplayName),
                u.Username = COALESCE($username, u.Username),
                u.Picture = COALESCE($picture, u.Picture)
            RETURN
                u
            """,
            parameters={
                "user_id": user_id,
                "display_name": display_name,
                "username": username,
                "picture": picture
            },
        )

        record = result.single()

        if record == None:
            Response(status_code=400, content="User does not exist")

        data = record[0]

        updated_user = {
            "user_id": data["UserID"],
            "display_name": data["DisplayName"],
            "username": data["Username"],
            "picture": data["Picture"],
        }
        return JSONResponse(updated_user)


 
@is_requester_privileged_for_user
async def delete_using_user_id(request: Request) -> JSONResponse:
    """
    Description: Deletes the user information with the associated user_id {user_id}. The {user_id}’s user_access_token needs to match the passed in user_access_token to be able to update the user. Returns error if failed.

    params:
        user_access_token: string

    return :

    """
    user_id = request.path_params["user_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")

    with get_neo4j_session() as session:
        result = session.run(
            """MATCH (u:User{UserID: $user_id})
            OPTIONAL MATCH (u)-[:user_host]->(e:Event) 
            DETACH DELETE u, e""",
            parameters={
                "user_id": user_id,
            },
        )

    return Response(status_code=200, content="User and events deleted")


 
async def get_event_host(request: Request) -> JSONResponse:
    """
    Description: Gets the host from {event_id}.

    params:
        user_access_token: string

    return :
        user_id: string,
        display_name: string,
        username: string,
        email: string,
        picture: string,

    """

    event_id = request.path_params["event_id"]

    body = await request.json()

    user_access_token = body["user_access_token"]
    try:
        assert all((event_id, user_access_token))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body")

    with get_neo4j_session() as session:
        result = session.run(
            """MATCH (e:Event{EventID : $event_id})<-[:user_host]-(u:User)
            RETURN u""",
            parameters={
                "event_id": event_id,
            },
        )

        record_timing(request, note="request time")

        record = result.single()

        if record == None:
            return Response(status_code=400, content="Event does not exist")

        data = record[0]

        user_data = {
            "user_id": data["UserID"],
            "display_name": data["DisplayName"],
            "username": data["Username"],
            "picture": data["Picture"],
        }

        return JSONResponse(user_data)


 
@is_requester_privileged_for_user
async def user_join_update(request: Request) -> JSONResponse:
    """
    Description: Modifies a join from {user_id} to {event_id}. Needs the {user_id}’s user_access_token to match the one passed into the body to be able to post the join.

    params:
        user_access_token: string
        did_join: boolean

    return :

        message: string

    """

    user_id = request.path_params["user_id"]
    event_id = request.path_params["event_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")
    did_join = body.get("did_join")

    try:
        assert all((user_id, event_id, user_access_token))
        assert type(did_join) == bool
    except AssertionError:
        return Response(status_code=400, content="Incomplete body or incorrect parameter")

    with get_neo4j_session() as session:
        result = session.run(
            """MATCH (u:User{UserID : $user_id, UserAccessToken: $user_access_token})-[r:user_join]->(e:Event{EventID: $event_id})
            RETURN r""",
            parameters={
                "user_access_token": user_access_token,
                "user_id": user_id,
                "event_id": event_id,
            },
        )

        record = result.single()

        if record != None:
            if did_join:
                return JSONResponse(
                    content={"message": "User already joined the event"},
                    status_code=200,
                )
            else:
                session.run(
                    """MATCH (u:User{UserID : $user_id})-[r:user_join]->(e:Event{EventID: $event_id})
                    DELETE r""",
                    parameters={
                        "user_id": user_id,
                        "event_id": event_id,
                    },
                )
                return JSONResponse(
                    content={"message": "Join removed successfully"}, status_code=200
                )
        else:
            if did_join:
                session.run(
                    """MATCH (u:User{UserID : $user_id}),(e:Event{EventID: $event_id}) 
                    CREATE (u)-[r:user_join]->(e)""",
                    parameters={
                        "user_id": user_id,
                        "event_id": event_id,
                    },
                )
                return JSONResponse(
                    content={"message": "Join created successfully"}, status_code=200
                )
            else:
                return JSONResponse(
                    content={"message": "User already did not join"}, status_code=200
                )


 
@is_requester_privileged_for_user
async def user_shoutout_update(request: Request) -> JSONResponse:
    """
    Description: Modifies a shoutout from {user_id} to {event_id}. Needs the {user_id}’s user_access_token to match the one passed into the body to be able to post the shoutout.

    params:
        user_access_token: string
        did_shoutout: boolean

    return :

        message: string

    """

    user_id = request.path_params["user_id"]
    event_id = request.path_params["event_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")
    did_shoutout = body.get("did_shoutout")

    try:
        assert all((user_id, event_id, user_access_token))
        assert type(did_shoutout) == bool
    except AssertionError:
        return Response(status_code=400, content="Incomplete body or incorrect parameter")

    with get_neo4j_session() as session:
        # check if user already gave a shoutout to the event
        result = session.run(
            """MATCH (u:User{UserID : $user_id, UserAccessToken: $user_access_token})-[r:user_shoutout]->(e:Event{EventID: $event_id})
            RETURN r""",
            parameters={
                "user_access_token": user_access_token,
                "user_id": user_id,
                "event_id": event_id,
            },
        )

        record = result.single()

        if record != None:
            if did_shoutout:
                return JSONResponse(
                    content={
                        "message": "User already gave a shoutout to the event"},
                    status_code=200,
                )
            else:
                session.run(
                    """MATCH (u:User{UserID : $user_id})-[r:user_shoutout]->(e:Event{EventID: $event_id})
                    DELETE r""",
                    parameters={
                        "user_id": user_id,
                        "event_id": event_id,
                    },
                )
                return JSONResponse(
                    content={"message": "shoutout removed successfully"},
                    status_code=200,
                )
        else:
            if did_shoutout:
                session.run(
                    """MATCH (u:User{UserID : $user_id}),(e:Event{EventID: $event_id})
                    CREATE (u)-[r:user_shoutout]->(e)""",
                    parameters={
                        "user_id": user_id,
                        "event_id": event_id,
                    },
                )
                return JSONResponse(
                    content={"message": "shoutout created successfully"},
                    status_code=200,
                )
            else:
                return JSONResponse(
                    content={"message": "User already did not give shoutout"},
                    status_code=200,
                )


 
@is_valid_user_access_token
async def get_all_school_users(request: Request) -> JSONResponse:

    """
    Description: Gets all of the users associated with a school of $school_id
    params:
        user_access_token: string

    return:

        [
        user_id: string,
        display_name: string,
        username: string,
        picture: string
        ]

    """

    school_id = request.path_params["school_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")

    try:
        assert all((school_id, user_access_token))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body")

    with get_neo4j_session() as session:

        result = session.run(
            """MATCH ((u:User)-[:user_school]->(s:School{SchoolID: $school_id}))
            RETURN {
                user_id: u.UserID,
                display_name: u.DisplayName,
                username: u.Username,
                picture: u.Picture
            } as user
            ORDER BY toLower(u.DisplayName)""",
            parameters={
                "school_id": school_id,
            },
        )

        users = []

        for record in result:
            user_data = record['user']
            user_id = user_data['user_id']
            display_name = user_data['display_name']
            username = user_data['username']
            picture = user_data['picture']

            users.append({
                "user_id": user_id,
                "display_name": display_name,
                "username": username,
                "picture": picture
            })

        return JSONResponse(
            users
        )


async def search_users(request: Request) -> JSONResponse:

    """
    Description: Gets all of the users associated with a school of $school_id
    params:
        user_access_token: string

    return:

        [
        user_id: string,
        display_name: string,
        username: string,
        picture: string
        ]

    """

    school_id = request.path_params["school_id"]
    query = request.path_params["query"]

    try:
        assert all((school_id, query))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body")

    with get_neo4j_session() as session:

        result = session.run(
            """MATCH ((u:User)-[:user_school]->(s:School{SchoolID: $school_id}))
                WHERE (toLower(u.DisplayName) CONTAINS toLower($query) OR toLower(u.Username) CONTAINS toLower($query))
            RETURN {
                user_id: u.UserID,
                display_name: u.DisplayName,
                username: u.Username,
                picture: u.Picture
            } as user
            ORDER BY toLower(u.DisplayName)
            LIMIT 10""",
            parameters={
                "school_id": school_id,
                "query": query,
            },
        )

        users = []

        for record in result:
            user_data = record['user']
            user_id = user_data['user_id']
            display_name = user_data['display_name']
            username = user_data['username']
            picture = user_data['picture']

            users.append({
                "user_id": user_id,
                "display_name": display_name,
                "username": username,
                "picture": picture
            })

        return JSONResponse(
            users
        )

routes = [
    Route(
        "/api_ver_1.0.0/user/user_access_token/{user_access_token}",
        get_using_user_access_token,
        methods=["GET"],
    ),
    Route(
        "/api_ver_1.0.0/user/user_id/{user_id}",
        get_using_user_id,
        methods=["GET"],
    ),
    Route(
        "/api_ver_1.0.0/user/user_id/{user_id}",
        update_using_user_id,
        methods=["UPDATE"],
    ),
    Route(
        "/api_ver_1.0.0/user/user_id/{user_id}",
        delete_using_user_id,
        methods=["DELETE"],
    ),
    Route(
        "/api_ver_1.0.0/user/event_id/{event_id}/host",
        get_event_host,
        methods=["POST"],
    ),
    Route(
        "/api_ver_1.0.0/user/user_id/{user_id}/event_id/{event_id}/join",
        user_join_update,
        methods=["UPDATE"],
    ),
    Route(
        "/api_ver_1.0.0/user/user_id/{user_id}/event_id/{event_id}/shoutout",
        user_shoutout_update,
        methods=["UPDATE"],
    ),
    Route("/api_ver_1.0.0/user/school_id/{school_id}",
          get_all_school_users,
          methods=["POST"],
          ),
    Route("/api_ver_1.0.0/user/school_id/{school_id}/search/{query}",
          search_users,
          methods=["GET"],
          ),
]
