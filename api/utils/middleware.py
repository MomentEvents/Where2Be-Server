from starlette.middleware.base import BaseHTTPMiddleware
from utils.models import Problem
from starlette.responses import Response


class ProblemHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Problem as problem:
            return Response(status_code=problem.status, content=problem.content)