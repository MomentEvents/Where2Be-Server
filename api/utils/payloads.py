# note: This file is unused, but it will be used in the future for refactoring

# payload objects are objects that convert a request body to an object and vice versa.

# there are payloads for users, events, interests, schools, and others

from dataclasses import dataclass
from typing import Any, Dict, List, Literal
import datetime

@dataclass
class EventCreationBody:
    user_access_token: str
    title: str
    description: str = field(
        default='',
        metadata={
            'validators': [validators.length(max=800)]
        }
    )
    location: str
    start_date_time: str
    end_date_time: str | None
    visibility: Literal['public', 'private']
    picture: str

@dataclass
class EventEditBody:
    user_access_token: str
    title: str
    description: str = field(
        default='',
        metadata={
            'validators': [validators.length(max=800)]
        }
    )
    location: str
    start_date_time: str
    end_date_time: str | None
    visibility: Literal['public', 'private']
    picture: str

