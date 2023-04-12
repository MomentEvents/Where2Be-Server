from starlette.applications import Starlette
from starlette.middleware import Middleware
from api import settings
from api.data import init_db, init_s3, close_s3
from api.endpoints import authservice, eventservice, interestservice, schoolservice, userservice
from api.utils.middleware import ProblemHandlingMiddleware
from api.utils.schema_gen import schema_route

if settings.DEBUG:
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    debugpy.wait_for_client()  # blocks execution until client is attached

routes = [
 *authservice, 
 *eventservice, 
 *interestservice, 
 *schoolservice, 
 *userservice,
]

middleware = [
    Middleware(ProblemHandlingMiddleware)
]

app = Starlette(debug=True, routes=routes, on_startup=[init_db, init_s3], on_shutdown=[close_s3], middleware=middleware)
app.mount("")