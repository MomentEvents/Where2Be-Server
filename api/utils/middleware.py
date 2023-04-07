from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

class ProblemHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        IS_DEBUG = True
        if IS_DEBUG:
            return await call_next(request)

        try:
            return await call_next(request)
        except:
            return Response(status_code=500, content="An internal server error occurred. Ple")