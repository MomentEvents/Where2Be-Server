from inspect import Parameter

from markupsafe import string
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route


from datetime import datetime
import bcrypt
import secrets
from common.models import Problem

from common.neo4j.moment_neo4j import get_neo4j_driver, run_neo4j_command
from api.version.ver_1_0_1.auth import is_real_user, is_requester_privileged_for_user

import platform

if platform.system() == "Windows":
    from asyncio.windows_events import NULL


async def get_all_interests(request: Request) -> JSONResponse:
    """
    Description: Gets all of the interests in the database.

    params:

    return :
        return: Array of… { interest_id: string,
                        name: string,
                        category: string,
            }
    """

    result = await run_neo4j_command(
        """MATCH (i:Interest) 
        RETURN i
        ORDER BY toLower(i.Name)""",
    )


    interest_array = []
    for record in result:

        if record == None:
            return Response(status_code=400, content="Interests do not exist")

        data = record[0]
        interest_array.append(
            {
                "interest_id": data["InterestID"],
                "name": data["Name"],
            }
        )

    print(interest_array)
    return JSONResponse(interest_array)
    
async def get_event_interest(request: Request) -> JSONResponse:
    """
    Description: Gets all interests from {event_id}. if event is private, user must be host to get this (for user_access_token)

    params:
        user_access_token: string,

    return: Array of… {
                        interest_id: string,
                        name: string,
                        category: string,
                }

    """

    event_id = request.path_params["event_id"]

    # body = await request.json()
    # user_access_token = body.get("user_access_token")

    try:
        assert all((event_id))
    except AssertionError:
        # Handle the error here
        print("Error")
        return Response(status_code=400, content="Parameter Missing")


    result = await run_neo4j_command(
        """MATCH (event:Event{EventID: $event_id})-[:event_tag]->(i:Interest) 
        RETURN i
        ORDER BY toLower(i.Name)""",
        parameters={"event_id": event_id},
    )

    interest_array = []

    for record in result:
        data = record[0]
        interest_array.append(
            {
                "interest_id": data["InterestID"],
                "name": data["Name"],
            }
        )

    return JSONResponse(interest_array)

routes = [
    Route("/interest",
        get_all_interests,
        methods=["GET"],
    ),
    Route("/interest/event_id/{event_id}",
        get_event_interest,
        methods=["POST"],
    ),
]
