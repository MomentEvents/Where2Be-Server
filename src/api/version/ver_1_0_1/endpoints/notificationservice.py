from common.models import Problem
from common.neo4j.commands.notificationcommands import add_push_token, get_notification_preferences, remove_push_token, set_notification_preferences
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from api.version.ver_1_0_1.auth import is_real_user, is_requester_privileged_for_user

@is_requester_privileged_for_user
async def add_user_notification_token(request: Request) -> JSONResponse:
    """
    
    body: {
        user_access_token: string,
        push_token: string,
        push_type: string,

    }
    """
    user_id = request.path_params["user_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")
    push_token = body.get("push_token")
    push_type = body.get("push_type")

    try:
        assert all((user_access_token, user_id, push_token, push_type))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body")

    print(str(push_token))
    print(type(push_token))
    print("Info up above ^")


    await add_push_token(user_id, push_token, push_type)

    return Response(status_code=200, content="Added push token")

@is_requester_privileged_for_user
async def remove_user_notification_token(request: Request) -> JSONResponse:
    """
    
    body: {
        user_access_token: string,
        push_token: string,
        push_type: string,
    }
    """
    user_id = request.path_params["user_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")
    push_token = body.get("push_token")
    push_type = body.get("push_type")


    try:
        assert all((user_access_token, user_id, push_token, push_type))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body")

    print(str(push_token))
    print(type(push_token))
    print("Info up above ^")

    await remove_push_token(user_id, push_token, push_type)

    return Response(status_code=200, content="Removed push token")

@is_requester_privileged_for_user
async def get_user_notification_preferences(request: Request) -> JSONResponse:
    """
    
    return: {
        followed_users: boolean
    }
    """
    user_id = request.path_params["user_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")


    try:
        assert all((user_access_token, user_id))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body")
    
    preferences = await get_notification_preferences(user_id)
    
    if(not preferences):
        raise Problem(status=400, content="Preferences do not exist. Either the user does not exist or there is some other error.")

    return JSONResponse(preferences)

@is_requester_privileged_for_user
async def set_user_notification_preferences(request: Request) -> JSONResponse:

    user_id = request.path_params["user_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")
    preferences = body.get("preferences")


    try:
        assert all((user_access_token, user_id, preferences))
    except AssertionError:
        return Response(status_code=400, content="Incomplete body")

    # We assume the set_notification_preferences handles this input checking for us

    result = await set_notification_preferences(user_id, preferences)
    if result is None or not result:
        raise Problem(status=400, content="Invalid notification preferences were given.")

    return Response(status_code=200, content="Updated notification preferences")

routes = [
    Route("/notification/user_id/{user_id}/add_token",
        add_user_notification_token,
        methods=["POST"],
    ),
    Route("/notification/user_id/{user_id}/remove_token",
        remove_user_notification_token,
        methods=["POST"],
    ),
    Route("/notification/user_id/{user_id}/get_preferences",
        get_user_notification_preferences,
        methods=["POST"],
    ),
    Route("/notification/user_id/{user_id}/set_preferences",
        set_user_notification_preferences,
        methods=["POST"],
    ),
]