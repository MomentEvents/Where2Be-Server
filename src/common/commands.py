import datetime
from dateutil import parser
import bcrypt
import secrets
import random

from common.neo4j.moment_neo4j import get_neo4j_session
from common.neo4j.converters import convert_user_entity_to_user, convert_school_entity_to_school
from common.s3.moment_s3 import get_bucket_url
from common.models import Problem
from common.utils import is_email
from common.firebase import login_user_firebase, create_user_firebase, get_firebase_user_by_uid, get_firebase_user_by_email, send_verification_email
from common.constants import IS_PROD

def create_user_entity(display_name: str, username: str, school_id: str, is_verified_org: bool):
    username = username.lower()
    username = username.strip()
    display_name = display_name.strip()

    random_number = str(random.randint(1, 5))
    default_user_image = (
        get_bucket_url()+"app-uploads/images/users/static/default" + random_number + ".png"
    )

    with get_neo4j_session() as session:

        user_access_token = secrets.token_urlsafe()
        user_id = secrets.token_urlsafe()

        result = session.run(
            """CREATE (u:User {UserID: $user_id, Username: $username, Picture:$picture, DisplayName:$display_name, UserAccessToken:$user_access_token, VerifiedOrganization:$is_verified_org})
            WITH u
            MATCH(n:School{SchoolID: $school_id})
            CREATE (u)-[r:user_school]->(n)
            RETURN u""",
            parameters={
                "username": username,
                "display_name": display_name,
                "picture": default_user_image,
                "school_id": school_id,
                "user_access_token": user_access_token,
                "user_id": user_id,
                "is_verified_org": is_verified_org,
            },
        )

        return user_access_token, user_id
 
def create_event_entity(user_access_token: str, event_image: str, title: str, description: str, location: str, visibility: str, interest_ids: [str], start_date_time_string, end_date_time_string):
    start_date_time = parser.parse(start_date_time_string).isoformat()
    end_date_time = None if end_date_time_string is None else parser.parse(end_date_time_string).isoformat()

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
                    StartDateTime: datetime($start_date_time),
                    EndDateTime: datetime($end_date_time),
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
def create_school_entity(school_id: str, name: str, abbreviation: str, latitude: float, longitude: float):
    with get_neo4j_session() as session:

        result = session.run(
            """CREATE (s:School {SchoolID: $school_id, Name: $name, Abbreviation: $abbreviation, Latitude: $latitude, Longitude: $longitude})
            RETURN s""",
            parameters={
                "school_id": school_id,
                "name": name,
                "abbreviation": abbreviation,
                "latitude": latitude,
                "longitude": longitude,
            },
        )

        return school_id

def get_school_entity_by_school_id(school_id: str):
    with get_neo4j_session() as session:
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
            return None

        data = record[0]

        school_data = convert_school_entity_to_school(data)

        return school_data



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

def create_push_token_entity(user_id: str, push_token: str, push_type: str):
    test = 1

def get_user_entity_by_username(username: str):
    with get_neo4j_session() as session:

        result = session.run(
            """MATCH (u:User {Username: $username})
            RETURN u""",
            parameters={
                "username": username
            },
        )

        record = result.single()

        if record == None:
            return None

        data = record[0]

        user_data = convert_user_entity_to_user(data)

        return user_data

def get_user_entity_by_user_id(user_id: str):
    with get_neo4j_session() as session:

        result = session.run(
            """MATCH (u:User {UserID: $user_id})
            RETURN u""",
            parameters={
                "user_id": user_id
            },
        )

        record = result.single()

        if record == None:
            return None

        data = record[0]

        user_data = convert_user_entity_to_user(data)

        return user_data

def login(usercred: str, password: str):
    # Check if it's a username or email

    email = usercred

    if(is_email(usercred) is False):

        # Get user by username
        user = get_user_entity_by_username(usercred)

        # If there is no user with the username
        if(user is None):
            raise Problem(status=400, content="Username does not exist")
        
        firebase_user = get_firebase_user_by_uid(user['user_id'])
        email = firebase_user.email
    
    result = login_user_firebase(email, password)

    print(result)
    if(result.get('error') is not None):
        message = result['error']['message']
        reason = ""
        if(message == "INVALID_EMAIL"):
            reason = "Email is not valid"
        elif(message == "EMAIL_NOT_FOUND"):
            reason = "Email does not exist"
        elif(message == "INVALID_PASSWORD"):
            reason = "Incorrect password"
        else:
            reason = "An unknown error occurred. Please report this!"

        raise Problem(status=400, content=reason)
    
    # successfully logged in
    user_id = result['localId']
    print("login success")

    # get user access token from user_id

    with get_neo4j_session() as session:

        result = session.run(
            """MATCH (u:User {UserID: $user_id})
            RETURN u""",
            parameters={
                "user_id": user_id
            },
        )

        record = result.single()
        data = record[0]

        return data['UserAccessToken']
        
def signup(username, display_name, email, password, school_id):

    username = username.lower()
    username = username.strip()
    display_name = display_name.strip()

    if len(password) < 7:
        raise Problem(status=400, content="Please enter a more complex password")

    if len(password) > 30:
        raise Problem(status=400, content="Your password is over 30 characters. Please enter a shorter password")

    result = get_firebase_user_by_email(email)
    if(result is not None):
        raise Problem(status=400, content="Email already exists")

    result = get_user_entity_by_username(username)
    if(result is not None):
        raise Problem(status=400, content="Username already exists")

    result = get_school_entity_by_school_id(school_id)
    if(result is None):
        raise Problem(status=400, content="School does not exist")


    is_verified_org = False

    # Create user in the database.
    user_access_token, user_id = create_user_entity(display_name, username, school_id, is_verified_org)

    # Create user in firebase
    result = create_user_firebase(user_id, email, password)
    send_verification_email(user_id)


    return user_access_token