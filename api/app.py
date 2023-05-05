import logging

from fastapi import FastAPI

from starlette.applications import Starlette
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

# Check if database is accessible

if test_neo4j_health() is not True:
    sys.exit(1)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ip4 = str(ipaddress.ip_address(8888))
# host = socket.gethostbyname(ip4)

# Get the ip_address of the machine
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

routes = [
    *ver_1_0_0.routes,
    *status.routes
]

app = FastAPI(debug=True, routes=routes, on_startup=[init_db])

@app.exception_handler(Exception)
async def internal_server_error(request: Request, exc: Exception):
    return Response(status_code=500, content="An internal server error occurred. Please contact support.")
    
add_timing_middleware(app, record=logger.info, prefix="app")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_headers=["*"])
app.add_exception_handler(Exception, internal_server_error)

# choose localhost or ipaddr
localhost = "127.0.0.1"
hosting = ip_address


if __name__ == "__main__":
    print("\n\nNow running Moment server on " + hosting + ":8080")
    # create database
    uvicorn.run(app, host=hosting, port=8080)
