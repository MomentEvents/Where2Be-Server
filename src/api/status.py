from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.routing import Route
from api.helpers import parse_request_data
from common.models import Problem
from common.utils import send_email
from common.sql.moment_sql import test_sql_health

async def get_health(request: Request) -> JSONResponse:
    return Response(status_code=200, content="Moment server is healthy")

async def get_compatability(request: Request) -> JSONResponse:

    request_data = await parse_request_data(request)
    print(request_data.get("app_version"))
    return Response(status_code=200, content="App version is compatible")
    # return Response(content="This version of Moment is not supported. Update to the latest version.", status_code=400)

async def test_1(request: Request) -> JSONResponse:
    # response = send_email("support@momentevents.app", "MomentAPI test", "This is from localhost tf\n\nThis is a newline\n\nhttps://momentevents.app")
    response = test_sql_health()
    return Response(status_code=200, content=str(response))

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
    Route(
        "/test_1",
        test_1,
        methods=["GET"],
    )
]