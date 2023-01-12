from functools import wraps
from starlette.requests import Request
from starlette.responses import JSONResponse

from api.neo4j_init import get_connection
from fastapi_utils.timing import record_timing


def check_user_access_token(func):
    @wraps(func)
    async def wrapper(request: Request) -> JSONResponse:
        body = await request.json()

        user_access_token = body.get("user_access_token")

        with get_connection() as session:
            result = session.run(
                """match (u:User{UserAccessToken: $user_access_token}) return u""",
                parameters={
                    "user_access_token": user_access_token,
                },
            )
            record = result.single()
            if record == None:
                return JSONResponse(
                    content={"message": "Invalid access token"}, status_code=401
                )

        record_timing(request, note="user access token check time")

        return await func(request)

    return wrapper
