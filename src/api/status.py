from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.routing import Route
from api.helpers import parse_request_data
from common.models import Problem

async def get_health(request: Request) -> JSONResponse:
    return Response(status_code=200, content="Where2Be server is healthy")

async def get_compatability(request: Request) -> JSONResponse:

    request_data = await parse_request_data(request)
    # print(request_data.get("app_version"))
    return Response(status_code=200, content="App version is compatible")

async def maintenance_response(request: Request) -> JSONResponse:
    return Response(status_code=503, content="We're currently upgrading our servers. Please come back in a bit!")

async def deprecated_response(request: Request) -> JSONResponse:
    return Response(status_code=404, content="Please update your app to the latest version of Where2Be on the app store")


routes = [
    # Route(
    #     "/{path:path}",
    #     maintenance_response,
    #     methods=["GET", "POST", "UPDATE", "DELETE",]
    # ),
    # Route("/",
    #     maintenance_response,
    #     methods=["GET", "POST", "UPDATE", "DELETE"],
    # ),
    Route("/",
        get_health,
        methods=["GET"],
    ),
    Route(
        "/app_compatability",
        get_compatability,
        methods=["POST"]
    ),
    Route(
        "/api_ver_1.0.0/{path:path}",
        deprecated_response,
        methods=["GET", "POST", "UPDATE", "DELETE"],
    )
]