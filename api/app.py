import logging

from fastapi import FastAPI

from starlette.applications import Starlette

from endpoints import (
    authservice,
    eventservice,
    userservice,
    schoolservice,
    interestservice,
)
import uvicorn
import socket
import ipaddress


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# # Get the ip_address of the machine
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

routes = [
    *authservice.routes,
    *eventservice.routes,
    *userservice.routes,
    *schoolservice.routes,
    *interestservice.routes,
]

app = FastAPI(debug=True, routes=routes)

# choose localhost or ipaddr
localhost = "127.0.0.1"
hosting = ip_address

if __name__ == "__main__":
    uvicorn.run(app, host=hosting, port=8080)
