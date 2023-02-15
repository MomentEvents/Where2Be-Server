from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.routing import Route

async def parse_request_data(request: Request):

    content_type = request.headers.get("Content-Type")
    semicolon_index = content_type.find(";")

    if semicolon_index != -1:
        content_type = content_type[:semicolon_index]

    if content_type == "application/json":
        request_data = await request.json()
        return request_data

    elif content_type == "multipart/form-data":
            request_data = await request.form()
            return request_data
    else:
        return None