from inspect import Parameter

from markupsafe import string
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from fastapi_utils.timing import record_timing

from datetime import datetime
import bcrypt
import secrets

from api.cloud_resources.moment_neo4j import get_connection
from api.version.ver_1_0_0.auth import is_real_user, is_requester_privileged_for_user

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

    with get_connection() as session:
        # check if email exists
        result = session.run(
            """match (i:Interest) return i""",
        )

        record_timing(request, note="request time")

        interest_array = []
        for record in result:

            if record == None:
                return Response(status_code=400, content="Interests do not exist")

            data = record[0]
            interest_array.append(
                {
                    "interest_id": data["InterestID"],
                    "name": data["Name"],
                    # "category": data["Category"],
                }
            )

        return JSONResponse(interest_array)


# async def get_interest(request: Request) -> JSONResponse:
#     """
#     Description: Gets a specific interest by its {interest_id}.

#     params:

#     return: {
#                 interest_id: string,
#                 name: string,
#                 category: string,
#             }

#     """

#     interest_id = request.path_params["interest_id"]

#     try:
#         assert all((interest_id))
#     except AssertionError:
#         # Handle the error here
#         print("Error")
#         return Response(status_code=400, content="Parameter Missing")

#     with get_connection() as session:
#         # check if email exists
#         result = session.run(
#             """match (i:Interest{InterestID : $interest_id}) return i""",
#             parameters={
#                 "interest_id": interest_id,
#             },
#         )

#         record_timing(request, note="request time")

#         # get the first element of object
#         record = result.single()

#         if record == None:
#             return Response(status_code=400, content="Interest does not exist")

#         data = record[0]

#         interest_data = {
#             "interest_id": data["InterestID"],
#             "name": data["Name"],
#             # "category": data["Category"],
#         }

#         return JSONResponse(interest_data)

# @is_requester_privileged_for_user
# async def get_user_interest(request: Request) -> JSONResponse:
#     """
#     Description: Gets all of a user’s interests. Needs the user_access_token to match.

#     params:

#     return: Array of… {
#                         interest_id: string,
#                         name: string,
#                         category: string,
#                 }

#     """

#     user_id = request.path_params["user_id"]

#     body = await request.json()

#     user_access_token = body.get("user_access_token")

#     try:
#         assert all((user_id))
#     except AssertionError:
#         # Handle the error here
#         print("Error")
#         return Response(status_code=400, content="Parameter Missing")

#     with get_connection() as session:
#         # check if email exists
#         result = session.run(
#             """match (u:User{UserID : $user_id, UserAccessToken: $user_access_token})-[:user_interest]->(i:Interest) return i""",
#             parameters={"user_id": user_id, "user_access_token": user_access_token},
#         )

#         record_timing(request, note="request time")

#         interest_array = []
#         for record in result:

#             if record == None:
#                 return Response(status_code=400, content="Interests do not exist")

#             data = record[0]
#             interest_array.append(
#                 {
#                     "interest_id": data["InterestID"],
#                     "name": data["Name"],
#                     # "category": data["Category"],
#                 }
#             )

#         return JSONResponse(interest_array)


# @is_requester_privileged_for_user
# async def update_user_interest(request: Request) -> JSONResponse:
#     """
#     Description: Deletes all interest connections from the user and makes all {interest_id} the connections that are attached to the user. user_access_token must match.

#     params:
#         user_access_token: string,
#         interest_id: string[]

#     return :

#     """

#     user_id = request.path_params["user_id"]

#     body = await request.json()

#     user_access_token = body.get("user_access_token")
#     interest_ids = body.get("interest_ids")
#     ###interest_ids

#     try:
#         assert all((user_id, user_access_token, interest_ids))
#     except AssertionError:
#         # Handle the error here
#         print("Error")
#         return Response(status_code=400, content="Parameter Missing")

#     with get_connection() as session:
#         # check if email exists
#         result = session.run(
#             """match (u:User{UserID : $user_id, UserAccessToken: $user_access_token})-[r:user_interest]->(i:Interest)
#             delete r
#             UNWIND $interest_ids as interest_id
#             MATCH (int:Interest {InterestID: interest_id})
#             CREATE (int)<-[ui:user_interest]-(u)
#             return ui""",
#             parameters={
#                 "user_id": user_id,
#                 "user_access_token": user_access_token,
#                 "interest_ids": interest_ids,
#             },
#         )

#         record_timing(request, note="request time")

#         # get the first element of object
#         record = result.single()

#         if record == None:
#             return Response(status_code=200, content="Unable to create connection")
#         else:
#             return Response(status_code=200, content="Interest connection created")

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

    with get_connection() as session:

        result = session.run(
            """MATCH (event:Event{EventID: $event_id})-[:event_tag]->(i:Interest) 
            RETURN i""",
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
    Route(
        "/api_ver_1.0.0/interest",
        get_all_interests,
        methods=["GET"],
    ),
    # Route(
    #     "/api_ver_1.0.0/interest/interest_id/{interest_id}",
    #     get_interest,
    #     methods=["GET"],
    # ),
    # Route(
    #     "/api_ver_1.0.0/interest/user_id/{user_id}",
    #     get_user_interest,
    #     methods=["POST"],
    # ),
    # Route(
    #     "/api_ver_1.0.0/interest/user_id/{user_id}",
    #     update_user_interest,
    #     methods=["UPDATE"],
    # ),
    Route(
        "/api_ver_1.0.0/interest/event_id/{event_id}",
        get_event_interest,
        methods=["POST"],
    ),
    # Route(
    #     "/api_ver_1.0.0/interest/event_id/{event_id}",
    #     update_event_interest,
    #     methods=["UPDATE"],
    # ),
]
