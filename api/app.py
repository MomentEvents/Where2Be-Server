import logging

from fastapi import FastAPI

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
# from multer import Multer, DiskStorage

from api.version.ver_1_0_0 import ver_1_0_0
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.routing import Route
import uvicorn
import socket
import ipaddress

from fastapi_utils.timing import add_timing_middleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ip4 = str(ipaddress.ip_address(8888))
# host = socket.gethostbyname(ip4)

# Get the ip_address of the machine
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

async def get_health(request: Request) -> JSONResponse:
    return Response(status_code=200, content="Moment server is healthy")

routes = [
    *ver_1_0_0.routes,
    Route("/",
        get_health,
        methods=["GET"],
    ),
]

app = FastAPI(debug=True, routes=routes)
add_timing_middleware(app, record=logger.info, prefix="app")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_headers=["*"])

# choose localhost or ipaddr
localhost = "127.0.0.1"
hosting = ip_address

if __name__ == "__main__":
    uvicorn.run(app, host=hosting, port=8080)