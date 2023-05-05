import datetime
from dateutil import parser
import bcrypt
import secrets
import random

from cloud_resources.moment_neo4j import get_neo4j_session
from cloud_resources.moment_s3 import get_bucket_url

from utils.models import Problem

def create_user_entity(display_name: str, username: str, email: str, password: str, verified_organization: bool, school_id: str):
    username = username.lower()
    username = username.strip()
    display_name = display_name.strip()
    if len(password) < 7:
        raise Problem(status=400, content="Please enter a more complex password")

    if len(password) > 30:
        raise Problem(status=400, content="Your password is over 30 characters. Please enter a shorter password")
    
    email_exists = False
    username_exists = False

    random_number = str(random.randint(1, 5))
    default_user_image = (
        get_bucket_url()+"app-uploads/images/users/static/default" + random_number + ".png"
    )

    with get_neo4j_session() as session:

        # check if username exists
        result = session.run(
            "MATCH (u:User {Username: $username}) RETURN u",
            parameters={"username": username},
        )
        record = result.single()
        if record != None:
            raise Problem(status=400, content="Username already exists")

        # check if school exists
        result = session.run(
            """
            MATCH(s:School{SchoolID: $school_id})
            RETURN s""",
            parameters={
                "school_id": school_id,
            },
        )
        record = result.single()
        if record == None:
            raise Problem(status=400, content="School does not exist")

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        user_access_token = secrets.token_urlsafe()
        user_id = secrets.token_urlsafe()

        result = session.run(
            """CREATE (u:User {UserID: $user_id, Username: $username, Picture:$picture, DisplayName:$display_name, PasswordHash:$hashed_password, UserAccessToken:$user_access_token})
            WITH u
            MATCH(n:School{SchoolID: $school_id})
            CREATE (u)-[r:user_school]->(n)
            RETURN u""",
            parameters={
                "username": username,
                "display_name": display_name,
                "picture": default_user_image,
                "hashed_password": hashed_password,
                "school_id": school_id,
                "user_access_token": user_access_token,
                "user_id": user_id,
            },
        )

        return user_access_token
 
def create_event_entity(user_access_token: str, event_image: str, title: str, description: str, location: str, visibility: str, interest_ids: [str], start_date_time: str, end_date_time: str):
    start_date_time = parser.parse(start_date_time)
    end_date_time = None if end_date_time is None else parser.parse(end_date_time)
    title = title.strip()
    location = location.strip()
    event_id = secrets.token_urlsafe()
    image_id = secrets.token_urlsafe()

    with get_neo4j_session() as session:
        result = session.run(
            """MATCH (user:User {UserAccessToken: $user_access_token})-[:user_school]->(school:School)
                CREATE (event:Event {
                    EventID: $event_id,
                    Title: $title,
                    Description: $description,
                    Picture: $image,
                    Location: $location,
                    StartDateTime: $start_date_time,
                    EndDateTime: $end_date_time,
                    Visibility: $visibility,
                    TimeCreated: datetime()
                })<-[:user_host]-(user),
                (event)-[:event_school]->(school)
                WITH user, event
                UNWIND $interest_ids as interest_id
                MATCH (tag:Interest {InterestID: interest_id})
                CREATE (tag)<-[:event_tag]-(event)""",
            parameters={
                "event_id": event_id,
                "user_access_token": user_access_token,
                "image": event_image,
                "title": title,
                "description": description,
                "location": location,
                "start_date_time": start_date_time,
                "end_date_time": end_date_time,
                "visibility": visibility,
                "interest_ids": interest_ids,
            },
        )

        return event_id

def create_school_entity(school_id: str, name: str, abbreviation: str):
    with get_neo4j_session() as session:

        result = session.run(
            """CREATE (s:School {SchoolID: $school_id, Name: $name, Abbreviation: $abbreviation})
            RETURN s""",
            parameters={
                "school_id": school_id,
                "name": name,
                "abbreviation": abbreviation,
            },
        )

        return school_id

def create_interest_entity(interest_id: str, name: str):
    with get_neo4j_session() as session:

        result = session.run(
            """CREATE (i:Interest {InterestID: $interest_id, Name: $name})
            RETURN i""",
            parameters={
                "interest_id": interest_id,
                "name": name,
            },
        )

        return interest_id