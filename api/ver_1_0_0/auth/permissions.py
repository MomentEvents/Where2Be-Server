from functools import wraps
from starlette.requests import Request
from starlette.responses import JSONResponse

from api.neo4j_init import get_connection
from fastapi_utils.timing import record_timing

# These are user access tokens that are administrators.
# They will be checked to see if a user is privileged on
# other endpoints
admin_user_access_tokens = {"TODO",}

# Note from kyle:
# Due to the fact that sometimes our requests
# are in formdata and others are in json, there
# is really no solid, consistent way to get parameters
# from our request without knowing the data type
# beforehand. So, these functions will not be wrappers
# for now, and they will simply be called in the body
# of other functions.

async def check_user_access_token(user_access_token) -> bool:

    with get_connection() as session:
        result = session.run(
            """match (u:User{UserAccessToken: $user_access_token}) return u""",
            parameters={
                "user_access_token": user_access_token,
            },
        )
        record = result.single()
        if record == None:
            return False

    return True

def is_user_privileged_for_event(user_access_token, event_id):
    return None

def is_user_privileged_for_user(user_access_token, user_id):
    return None


def is_user_privileged(user_access_token) -> bool:

    return True
