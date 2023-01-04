import logging

from fastapi import FastAPI

from starlette.applications import Starlette

from endpoints import authservice
import uvicorn
import socket
import ipaddress

from fastapi_utils.timing import add_timing_middleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ip4 = str(ipaddress.ip_address(8888))
# host = socket.gethostbyname(ip4)

# # Get the ip_address of the machine
# hostname = socket.gethostname()
# ip_address = socket.gethostbyname(hostname)

routes = [
    *authservice.routes,
]

app = FastAPI(debug=True, routes=routes)
add_timing_middleware(app, record=logger.info, prefix="app")

# choose localhost or ipaddr
localhost = "127.0.0.1"
hosting = localhost

if __name__ == "__main__":
    uvicorn.run(app, host=hosting, port=8080)
