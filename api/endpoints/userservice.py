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

from api.neo4j_init import get_connection
from api.auth import check_user_access_token

import platform

if platform.system() == "Windows":
    from asyncio.windows_events import NULL


# error handling for broken queries!


def get_hash_pwd(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


@check_user_access_token
async def get_using_user_access_token(request: Request) -> JSONResponse:
    """
    Description: Gets the user information with the associated user_access_token {user_access_token}. Returns error if no results found.

    params:
        user_access_token: string

    return :
        user_id: string,
        display_name: string,
        username: string,
        email: string,
        picture: string,

    """

    user_access_token = request.path_params["user_access_token"]

    try:
        assert all((user_access_token))
    except AssertionError:
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Parameter Missing")

    with get_connection() as session:
        # check if email exists
        result = session.run(
            """match (u:User{UserAccessToken : $user_access_token}) return u""",
            parameters={
                "user_access_token": user_access_token,
            },
        )

        record_timing(request, note="request time")

        # get the first element of object
        record = result.single()

        if record == None:
            return Response(status_code=400, content="User does not exist")

        data = record[0]

        user_data = {
            "user_id": data["UserID"],
            "display_name": data["Name"],
            "username": data["Username"],
            "email": data["Email"],
            "picture": data["Picture"],
        }

        return JSONResponse(user_data)


@check_user_access_token
async def get_using_user_id(request: Request) -> JSONResponse:
    """
    Description: Gets the user information with the associated user_id {user_id}. Returns error if no results found.

    params:
        user_id: string

    return :
        user_id: string,
        display_name: string,
        username: string,
        email: string,
        picture: string,

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
            """match (u:User{UserID : $user_id}) return u""",
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

        user_data = {
            "user_id": data["UserID"],
            "display_name": data["Name"],
            "username": data["Username"],
            "email": data["Email"],
            "picture": data["Picture"],
        }

        return JSONResponse(user_data)


@check_user_access_token
async def update_using_user_id(request: Request) -> JSONResponse:
    """
    Description: Updates the user information with the associated user_id {user_id}. The {user_id}’s user_access_token needs to match the passed in user_access_token to be able to update the user. Returns error if failed.

    params:
        user_id: string

    return :
        user_id: string,
        display_name: string,
        username: string,
        email: string,
        picture: string,

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
            """match (u:User{UserID : $user_id}) return u""",
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

        user_data = {
            "user_id": data["UserID"],
            "display_name": data["Name"],
            "username": data["Username"],
            "email": data["Email"],
            "picture": data["Picture"],
        }

        return JSONResponse(user_data)


@check_user_access_token
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

    try:
        assert all((user_id))
    except AssertionError:
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Parameter Missing")

    with get_connection() as session:
        # check if email exists
        result = session.run(
            """match (u:User{UserID : $user_id, UserAccessToken: $user_access_token}) return u""",
            parameters={
                "user_id": user_id,
                "user_access_token": user_access_token,
            },
        )

        record_timing(request, note="request time")

        # get the first element of object
        record = result.single()

        if record == None:
            return Response(status_code=400, content="User does not exist")

        result = session.run(
            """match (u:User{UserID : $user_id, UserAccessToken: $user_access_token}) delete u""",
            parameters={
                "user_id": user_id,
                "user_access_token": user_access_token,
            },
        )

        return Response(status_code=200, content="user deleted")


@check_user_access_token
async def user_did_join(request: Request) -> JSONResponse:
    """
    Description: Gets whether a user has joined a specific event already. Needs the {user_id}’s user_access_token to match the one passed into the body to get the join.

    params:
        user_access_token: string

    return :

        did_join: boolean

    """

    user_id = request.path_params["user_id"]
    event_id = request.path_params["event_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")

    try:
        assert all((user_id))
    except AssertionError:
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Parameter Missing")

    with get_connection() as session:
        # check if email exists
        result = session.run(
            """match (u:User{UserID : $user_id, UserAccessToken: $user_access_token})-[:user_join]->(e:Event{EventID: $event_id}) return u""",
            parameters={
                "user_access_token": user_access_token,
                "user_id": user_id,
                "event_id": event_id,
            },
        )

        record_timing(request, note="request time")

        # get the first element of object
        record = result.single()

        if record == None:
            return JSONResponse(content={"did_join": False}, status_code=200)

        # if record["u"]["UserAccessToken"] != user_access_token:
        #     return JSONResponse(content={"did_join": False}, status_code=200)

        return JSONResponse(content={"did_join": True}, status_code=200)


# @check_user_access_token
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

    # return JSONResponse(content=str(did_join == False), status_code=200)

    try:
        assert all((user_id, event_id, user_access_token))
        assert type(did_join) == bool
    except AssertionError:
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Parameter Error or Missing")

    with get_connection() as session:
        # check if user already joined the event
        result = session.run(
            """match (u:User{UserID : $user_id, UserAccessToken: $user_access_token})-[r:user_join]->(e:Event{EventID: $event_id}) return r""",
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
                    """match (u:User{UserID : $user_id})-[r:user_join]->(e:Event{EventID: $event_id}) delete r""",
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
                    """match (u:User{UserID : $user_id}),(e:Event{EventID: $event_id}) create (u)-[r:user_join]->(e)""",
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


@check_user_access_token
async def user_did_shoutout(request: Request) -> JSONResponse:
    """
    Description: Checks if {user_id} has shouted out {event_id} already. Needs the {user_id}’s user_access_token to match the one passed into the body to be able to access the shoutout.
    params:
        user_access_token: string

    return :

        did_shoutout: boolean

    """

    user_id = request.path_params["user_id"]
    event_id = request.path_params["event_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")

    try:
        assert all((user_id))
    except AssertionError:
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Parameter Missing")

    with get_connection() as session:
        # check if email exists
        result = session.run(
            """match (u:User{UserID : $user_id, UserAccessToken: $user_access_token})-[:user_shoutout]->(e:Event{EventID: $event_id}) return u""",
            parameters={
                "user_access_token": user_access_token,
                "user_id": user_id,
                "event_id": event_id,
            },
        )

        record_timing(request, note="request time")

        # get the first element of object
        record = result.single()

        if record == None:
            return JSONResponse(content={"did_shoutout": False}, status_code=200)

        # if record["u"]["UserAccessToken"] != user_access_token:
        #     return JSONResponse(content={"did_join": False}, status_code=200)

        return JSONResponse(content={"did_shoutout": True}, status_code=200)


# @check_user_access_token
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
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Parameter Error or Missing")

    with get_connection() as session:
        # check if user already gave a shoutout to the event
        result = session.run(
            """match (u:User{UserID : $user_id, UserAccessToken: $user_access_token})-[r:user_shoutout]->(e:Event{EventID: $event_id}) return r""",
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
                    content={"message": "User already gave a shoutout to the event"},
                    status_code=200,
                )
            else:
                session.run(
                    """match (u:User{UserID : $user_id})-[r:user_shoutout]->(e:Event{EventID: $event_id}) delete r""",
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
                    """match (u:User{UserID : $user_id}),(e:Event{EventID: $event_id}) create (u)-[r:user_shoutout]->(e)""",
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
        "/api_ver_1.0.0/user/user_id/{user_id}/event_id/{event_id}/join/",
        user_did_join,
        methods=["POST"],
    ),
    Route(
        "/api_ver_1.0.0/user/user_id/{user_id}/event_id/{event_id}/join/",
        user_join_update,
        methods=["UPDATE"],
    ),
    Route(
        "/api_ver_1.0.0/user/user_id/{user_id}/event_id/{event_id}/shoutout/",
        user_did_shoutout,
        methods=["POST"],
    ),
    Route(
        "/api_ver_1.0.0/user/user_id/{user_id}/event_id/{event_id}/shoutout/",
        user_shoutout_update,
        methods=["UPDATE"],
    ),
]
