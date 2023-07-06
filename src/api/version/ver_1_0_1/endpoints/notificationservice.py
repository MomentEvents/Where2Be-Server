from common.neo4j.commands.notificationcommands import add_push_token, remove_push_token
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


    add_push_token(user_id, push_token, push_type)

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

    remove_push_token(user_id, push_token, push_type)

    return Response(status_code=200, content="Removed push token")

routes = [
    Route("/notification/user_id/{user_id}/add_token",
        add_user_notification_token,
        methods=["POST"],
    ),
    Route("/notification/user_id/{user_id}/add_token",
        add_user_notification_token,
        methods=["POST"],
    )
]