from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from api.utils.responses import ProblemResponse
from api.settings import IS_DEBUG

class ProblemHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Problem as problem:
            if IS_DEBUG:
                return Response(status_code=500, content=str(problem))
            else:
                return Response(status_code=500, content="An internal server error occurred")