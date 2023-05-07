from starlette.middleware.base import BaseHTTPMiddleware
from utils.models import Problem
from starlette.responses import Response
from debug import IS_DEBUG
import traceback


class ProblemHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Problem as problem:
            return Response(status_code=problem.status, content=problem.content)
        except Exception as e:  # Catch all other exceptions
            if IS_DEBUG is False:
                return Response(status_code=500, content="An unknown server error occurred. Please report this issue to support.")
            else:
                stack_trace = traceback.format_exc()
                return Response(status_code=500, content="AN INTERNAL SERVER ERROR OCCURRED! \n\n\n" + stack_trace)