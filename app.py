from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn
import socket

localhost = 'localhost'
ipaddr = socket.gethostbyname(socket.gethostname())

# choose localhost or ipaddr
hosting = ipaddr

async def homepage(request):
    return JSONResponse({'hello': 'world'})


app = Starlette(debug=True, routes=[
    Route('/', homepage),
])

if __name__ == "__main__":
    uvicorn.run(app, host=hosting, port=8080)