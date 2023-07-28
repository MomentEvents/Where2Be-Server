from inspect import Parameter

from markupsafe import string
from common.firebase import delete_firebase_user_by_uid, get_firebase_user_by_uid
from common.neo4j.commands.usercommands import create_follow_connection, create_join_connection, create_not_interested_connection, create_shoutout_connection, create_viewed_connections, delete_follow_connection, delete_join_connection, delete_not_interested_connection, delete_shoutout_connection, get_user_entity_by_user_access_token, get_user_entity_by_user_id, get_user_entity_by_username
from common.neo4j.converters import convert_user_entity_to_user
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from common.models import Problem
from typing import List
import time


from datetime import datetime
import secrets

from common.neo4j.moment_neo4j import get_neo4j_session
from api.version.ver_1_0_1.auth import is_real_user, is_requester_privileged_for_user, is_user_formatted, is_valid_user_access_token

from common.s3.moment_s3 import upload_base64_image

async def get_using_user_access_token(request: Request) -> JSONResponse:
    # raise Problem(status=400, content="Please log in to continue")
    """
    Description: Gets the user information with the associated user_access_token {user_access_token}. Returns error if no results found.

    params:
        user_access_token: string

    return :
        user_id: string,
        display_name: string,
        username: string,
        picture: string,
        verified_organization: boolean,
    """

    user_access_token = request.path_params["user_access_token"]

    try:
        assert all((user_access_token))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body")

    user = get_user_entity_by_user_access_token(user_access_token=user_access_token, show_num_events_followers_following=True)

    if(user is None):
        raise Problem(status=400, content="User does not exist")
    
    return JSONResponse(user)

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
        verified_organization: boolean,

    """

    user_id = request.path_params["user_id"]

    try:
        assert all((user_id))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body")

    user = get_user_entity_by_user_id(user_id=user_id, self_user_access_token=None, show_num_events_followers_following=True)

    if(user is None):
        raise Problem(status=400, content="User does not exist")
    
    return JSONResponse(user)

async def get_using_user_id_with_body(request: Request) -> JSONResponse:
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

    print("CALLING GET_USING_USER_ID_WITH_BODY")
    begin_start_time = time.perf_counter()

    user_id = request.path_params["user_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")

    try:
        assert all((user_id, user_access_token))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body")
    
    start_time = time.perf_counter()
    
    user = get_user_entity_by_user_id(user_id=user_id, self_user_access_token=user_access_token, show_num_events_followers_following=True)
    
    end_time = time.perf_counter()
    elapsed_time_ms = (end_time - start_time) * 1000  # convert to milliseconds

    print("took ", str(elapsed_time_ms), " milliseconds for getting profile by user_id") 

    elapsed_time_ms = (start_time - begin_start_time) * 1000  # convert to milliseconds

    print("took ", str(elapsed_time_ms), " milliseconds before calling query to get by user_id") 
    
    if(user is None):
        raise Problem(status=400, content="User does not exist")
    return JSONResponse(user)

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

    user = get_user_entity_by_user_access_token(user_access_token, False)

    if(user["username"] != username):
        user_with_username = get_user_entity_by_username(username)
        if(user_with_username is not None):
            return Response(status_code=400, content="A user with this username already exists")


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
            "verified_organization": data["VerifiedOrganization"],
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

    delete_firebase_user_by_uid(user_id)

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
        picture: string,
        verified_organization: boolean,

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


        record = result.single()

        if record == None:
            return Response(status_code=400, content="Event does not exist")

        data = record[0]

        user_data = convert_user_entity_to_user(data=data, show_num_events_followers_following=False)

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

    if(did_join):
        create_join_connection(user_id, event_id)
    else:
        delete_join_connection(user_id, event_id)
    
    return Response(status_code=200)

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

    if(did_shoutout):
        create_shoutout_connection(user_id, event_id)
    else:
        delete_shoutout_connection(user_id, event_id)
    
    return Response(status_code=200)

@is_requester_privileged_for_user
async def user_not_interested_update(request: Request) -> JSONResponse:
    """
    body of user_access_token, not_interested
    path params of user_id, to_user_id
    """

    user_id = request.path_params["user_id"]
    event_id = request.path_params["event_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")
    did_not_interested = body.get("did_not_interested")

    try:
        assert all((user_id, user_access_token))
        assert type(did_not_interested) == bool
    except AssertionError:
        return Response(status_code=400, content="Incomplete body or incorrect parameter")

    if(did_not_interested):
        create_not_interested_connection(user_id, event_id)
    else:
        delete_not_interested_connection(user_id, event_id)
    
    return Response(status_code=200)

# @is_requester_privileged_for_user
# async def user_viewed_update(request: Request) -> JSONResponse:
#     """
#     body of user_access_token, not_interested
#     path params of user_id, to_user_id
#     """

#     user_id = request.path_params["user_id"]

#     body = await request.json()

#     user_access_token = body.get("user_access_token")
#     event_ids = body.get("event_ids")

#     print(type(event_ids))
#     try:
#         assert all((user_id, user_access_token, event_ids))
#         assert type(event_ids) == list
#     except AssertionError:
#         return Response(status_code=400, content="Incomplete body or incorrect parameter")

#     create_viewed_connections(user_id, event_ids)
    
#     return Response(status_code=200)

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
    
    with get_neo4j_session() as session:

        result = session.run(
            """MATCH ((u:User)-[:user_school]->(s:School{SchoolID: $school_id}))
                WHERE (toLower(u.DisplayName) CONTAINS toLower($query) OR toLower(u.Username) CONTAINS toLower($query))
            RETURN u
            ORDER BY toLower(u.DisplayName)
            LIMIT 20""",
            parameters={
                "school_id": school_id,
                "query": query,
            },
        )

        users = []

        for record in result:
            user_data = record["u"]
            users.append(convert_user_entity_to_user(data=user_data, show_num_events_followers_following=False))

        return JSONResponse(
            users
        )

@is_requester_privileged_for_user
async def user_follow_update(request: Request) -> JSONResponse:
    """
    body of user_access_token, did_follow
    path params of user_id, to_user_id
    """

    user_id = request.path_params["user_id"]
    to_user_id = request.path_params["to_user_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")
    did_follow = body.get("did_follow")

    try:
        assert all((user_id, to_user_id, user_access_token))
        assert (user_id != to_user_id)
        assert type(did_follow) == bool
    except AssertionError:
        return Response(status_code=400, content="Incomplete body or incorrect parameter")

    if(did_follow):
        create_follow_connection(user_id, to_user_id)
    else:
        delete_follow_connection(user_id, to_user_id)
    
    return Response(status_code=200)

@is_requester_privileged_for_user
async def get_user_email(request: Request) -> JSONResponse:

    user_id = request.path_params["user_id"]

    try:
        assert all((user_id))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body")
    
    firebase_user = get_firebase_user_by_uid(uid=user_id)

    email = firebase_user.email
    email_verified = firebase_user.email_verified

    if(email is None):
        raise Problem(status_code=400,content="Could not retrieve email for user")

    return JSONResponse({"email": email, "email_verified": email_verified})

async def get_following_list(request: Request) -> JSONResponse:
    """
    body: {
        user_access_token,
        user_id_cursor (optional)
    }
    return: {
        list of users without their followers and following
    }
    """

    user_id = request.path_params["user_id"]

    body = await request.json()
    user_access_token = body.get("user_access_token")
    cursor = body.get("user_id_cursor")  # Cursor (user_id) could be None.

    try:
        assert all((user_id, user_access_token))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body")
    
    with get_neo4j_session() as session:
        cursor_timestamp = None

        # If a cursor is provided, get its associated timestamp.
        if cursor:
            cursor_query = """
                MATCH (cursor_follower:User)<-[cursor_follow:user_follow]-(user:User{UserID: $user_id})
                WHERE cursor_follower.UserID = $cursor
                RETURN cursor_follow.Timestamp as timestamp
            """
            cursor_result = session.run(
                cursor_query,
                parameters={
                    "user_id": user_id,
                    "cursor": cursor,
                },
            )

            for record in cursor_result:
                cursor_timestamp = record["timestamp"]

        # Now use the cursor timestamp (if any) to filter the main query.
        if cursor_timestamp:
            main_query = """
                MATCH (follower:User)<-[follow:user_follow]-(user:User{UserID: $user_id})
                WHERE follow.Timestamp < datetime($cursor_timestamp) AND follower.UserID <> $cursor
                RETURN follower
                ORDER BY follow.Timestamp DESC
                LIMIT 20
            """
        else:
            main_query = """
                MATCH (follower:User)<-[follow:user_follow]-(user:User{UserID: $user_id})
                RETURN follower
                ORDER BY follow.Timestamp DESC
                LIMIT 20
            """

        result = session.run(
            main_query,
            parameters={
                "user_id": user_id,
                "cursor": cursor,
                "cursor_timestamp": cursor_timestamp,
            },
        )

        users = []

        for record in result:
            user_data = record["follower"]
            users.append(convert_user_entity_to_user(data=user_data, show_num_events_followers_following=False))

        return JSONResponse(
            users
        )

async def get_follower_list(request: Request) -> JSONResponse:

    """
    body: {
        user_access_token,
        user_id_cursor (optional)
    }
    return: {
        list of users without their followers and following
    }
    """

    user_id = request.path_params["user_id"]

    body = await request.json()
    user_access_token = body.get("user_access_token")
    cursor = body.get("user_id_cursor")  # Cursor (user_id) could be None.

    try:
        assert all((user_id, user_access_token))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body")
    
    with get_neo4j_session() as session:
        cursor_timestamp = None

        # If a cursor is provided, get its associated timestamp.
        if cursor:
            cursor_query = """
                MATCH (cursor_follower:User)-[cursor_follow:user_follow]->(user:User{UserID: $user_id})
                WHERE cursor_follower.UserID = $cursor
                RETURN cursor_follow.Timestamp as timestamp
            """
            cursor_result = session.run(
                cursor_query,
                parameters={
                    "user_id": user_id,
                    "cursor": cursor,
                },
            )

            for record in cursor_result:
                cursor_timestamp = record["timestamp"]

        # Now use the cursor timestamp (if any) to filter the main query.
        if cursor_timestamp:
            main_query = """
                MATCH (follower:User)-[follow:user_follow]->(user:User{UserID: $user_id})
                WHERE follow.Timestamp < datetime($cursor_timestamp) AND follower.UserID <> $cursor
                RETURN follower
                ORDER BY follow.Timestamp DESC
                LIMIT 20
            """
        else:
            main_query = """
                MATCH (follower:User)-[follow:user_follow]->(user:User{UserID: $user_id})
                RETURN follower
                ORDER BY follow.Timestamp DESC
                LIMIT 20
            """

        result = session.run(
            main_query,
            parameters={
                "user_id": user_id,
                "cursor": cursor,
                "cursor_timestamp": cursor_timestamp,
            },
        )

        users = []

        for record in result:
            user_data = record["follower"]
            users.append(convert_user_entity_to_user(data=user_data, show_num_events_followers_following=False))

        return JSONResponse(
            users
        )

routes = [
    Route("/user/user_access_token/{user_access_token}",
        get_using_user_access_token,
        methods=["GET"],
    ),
    Route("/user/user_id/{user_id}",
        get_using_user_id,
        methods=["GET"],
    ),
    Route("/user/user_id/{user_id}",
        get_using_user_id_with_body,
        methods=["POST"],
    ),
    Route("/user/user_id/{user_id}",
        update_using_user_id,
        methods=["UPDATE"],
    ),
    Route("/user/user_id/{user_id}",
        delete_using_user_id,
        methods=["DELETE"],
    ),
    Route("/user/event_id/{event_id}/host",
        get_event_host,
        methods=["POST"],
    ),
    Route("/user/user_id/{user_id}/event_id/{event_id}/join",
        user_join_update,
        methods=["UPDATE"],
    ),
    Route("/user/user_id/{user_id}/event_id/{event_id}/shoutout",
        user_shoutout_update,
        methods=["UPDATE"],
    ),
    Route("/user/user_id/{user_id}/event_id/{event_id}/not_interested",
        user_not_interested_update,
        methods=["UPDATE"],
    ),
    # Route("/user/user_id/{user_id}/set_viewed_events",
    #     user_viewed_update,
    #     methods=["UPDATE"],
    # ),
    Route("/user/school_id/{school_id}/search",
          search_users,
          methods=["POST"],
    ),
    Route("/user/user_id/{user_id}/follow/user_id/{to_user_id}",
          user_follow_update,
          methods=["UPDATE"],
    ),
    Route("/user/user_id/{user_id}/get_email",
          get_user_email,
          methods=["POST"],
    ),
    Route("/user/user_id/{user_id}/followers",
          get_follower_list,
          methods=["POST"],
    ),
    Route("/user/user_id/{user_id}/following",
          get_following_list,
          methods=["POST"],
    ),
]
