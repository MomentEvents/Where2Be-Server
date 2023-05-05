import logging

from fastapi import FastAPI

from starlette.applications import Starlette
from starlette.middleware import Middleware

from starlette.middleware.cors import CORSMiddleware
# from multer import Multer, DiskStorage

from version.ver_1_0_0 import ver_1_0_0
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.routing import Route
import uvicorn
import socket
import ipaddress
from builtins import Exception

from fastapi_utils.timing import add_timing_middleware

import status

from database_resources.data import init_db
from cloud_resources.moment_neo4j import get_neo4j_session, test_neo4j_health
import sys
from utils.middleware import ProblemHandlingMiddleware

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

routes = [
    *ver_1_0_0.routes,
    *status.routes
]

middleware = [
    Middleware(ProblemHandlingMiddleware)
]

app = Starlette(debug=True, routes=routes, on_startup=[init_db], middleware=middleware)

if __name__ == "__main__":
    print("\n\nNow running Moment server on " + hosting + ":8080")

    uvicorn.run(app, host=ip_address, port=8080)
