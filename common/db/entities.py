# Entities are nodes and edges that are within the database. 

# user_host

# user_shoutout

# constructor for edges is user_shoutout(from, to)

from dataclasses import dataclass
from typing import Any, Dict, List
import datetime

@dataclass
class User:
    UserID: str # unique
    Username: str # unique
    Email: str # unique
    UserAccessToken: str
    DisplayName: str
    PasswordHash: object
    Picture: str

@dataclass
class Event:
    EventID: str # unique
    Title: str
    Description: str
    Picture: str
    Location: str
    StartDateTime: datetime
    EndDateTime: datetime | None
    Visibility: str
    TimeCreated: datetime

@dataclass
class School:
    SchoolID: str # unique
    Name: str
    Abbreviation: str
    Latitude: float
    Longitude: float

@dataclass
class Intrest:
    InterestID: str # unique
    Name: str

@dataclass
class user_shoutout:
    UserID: str # from
    EventID: str # to

@dataclass
class user_join:
    UserID: str # from
    EventID: str # to

@dataclass
class user_host:
    UserID: str # from
    EventID: str # to

@dataclass
class user_school:
    UserID: str # from
    SchoolID: str # to

@dataclass
class event_school:
    EventID: str # from
    SchoolID: str # to

@dataclass
class event_tag:
    EventID: str # from
    InterestID: str # to