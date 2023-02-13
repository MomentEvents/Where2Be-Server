from version.ver_1_0_1.endpoints import (
    authservice,
    eventservice,
    userservice,
    schoolservice,
    interestservice
)

routes = [
    *authservice.routes,
    *eventservice.routes,
    *userservice.routes,
    *schoolservice.routes,
    *interestservice.routes,
]