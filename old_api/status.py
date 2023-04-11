from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.routing import Route
from helpers import parse_request_data

async def get_health(request: Request) -> JSONResponse:
    return Response(status_code=200, content="Moment server is healthy")

async def get_compatability(request: Request) -> JSONResponse:

    request_data = await parse_request_data(request)
    print(request_data.get("app_version"))
    return Response(status_code=200, content="App version is compatible")
    # return Response(content="This version of Moment is not supported. Update to the latest version.", status_code=400)

routes = [
    Route("/",
        get_health,
        methods=["GET"],
    ),
    Route(
        "/app_compatability",
        get_compatability,
        methods=["POST"]
    ),
]