import logging

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount

from starlette.middleware.cors import CORSMiddleware

from api.version.ver_1_0_1 import ver_1_0_1
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.routing import Route
import uvicorn
import socket
import ipaddress
from builtins import Exception

from api import status
from common.neo4j.data import init_neo4j
from common.neo4j.moment_neo4j import get_neo4j_session, test_neo4j_health
import sys
from api.utils.middleware import ProblemHandlingMiddleware

routes = [
    Mount('/v1.0.1', routes=[*ver_1_0_1.routes]),
    *status.routes
]

middleware = [
    Middleware(ProblemHandlingMiddleware)
]

app = Starlette(debug=True, routes=routes, on_startup=[init_neo4j], middleware=middleware)