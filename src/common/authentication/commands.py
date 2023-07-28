from api.helpers import get_email_domain
from common.neo4j.commands.usercommands import create_user_entity, get_user_entity_by_username
from common.neo4j.commands.schoolcommands import get_school_entity_by_email_domain, get_school_entity_by_school_id
from common.neo4j.moment_neo4j import get_neo4j_session, parse_neo4j_data, run_neo4j_query
from common.models import Problem
from common.utils import is_email
from common.firebase import login_user_firebase, create_user_firebase, get_firebase_user_by_uid, get_firebase_user_by_email, send_verification_email
from common.constants import IS_PROD

enable_firebase = True # If disabled, you can manually pass in a user access token and user id

async def login(usercred: str, password: str):

    if(not enable_firebase):
        user_access_token = "gHL9LK-4bgALRzdNJFW5KZWkMdBmxrfQCnjdhZRpYG4"
        user_id = "Ez7o28WpYX2bsrri0udD9xtNzv7SzC_D3FCjPnjv21g"
        return user_id, user_access_token
    # Check if it's a username or email

    usercred = usercred.lower()
    usercred = usercred.strip()

    email = usercred    
    if(not is_email(usercred)):

        # Get user by username
        user = await get_user_entity_by_username(usercred)

        # If there is no user with the username
        if(user is None):
            raise Problem(status=400, content="An account with this username does not exist")
        
        user_id = user['user_id']

        firebase_user = get_firebase_user_by_uid(user_id)

        if(firebase_user is None):
            raise Problem(status=400, content="This specific account does not have an email linked to it. Please contact support to resolve this issue")
        
        email = firebase_user.email
    else:
        # usercred is email
        firebase_user = get_firebase_user_by_email(usercred)

        if (firebase_user is None):
            raise Problem(status=400, content="An account with this email does not exist")

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
            reason = "An unknown error occurred. Please report this to support"

        raise Problem(status=400, content=reason)
    
    # successfully logged in
    user_id = result['localId']
    print("login success")

    # get user access token from user_id

    result = await run_neo4j_query(
        """MATCH (u:User {UserID: $user_id})
        RETURN u""",
        parameters={
            "user_id": user_id
        },
    )

    data = parse_neo4j_data(result, 'single')

    if(result is None):
        raise Problem(status=400, content="There is no user associated with this returned UserID. Please contact support to resolve this issue")

    print("user_id ", user_id)
    print("user_access_token ", data['UserAccessToken'])

    return user_id, data['UserAccessToken']
        
async def signup(username, display_name, email, password):
    if(not enable_firebase):
        user_access_token = "gHL9LK-4bgALRzdNJFW5KZWkMdBmxrfQCnjdhZRpYG4"
        user_id = "Ez7o28WpYX2bsrri0udD9xtNzv7SzC_D3FCjPnjv21g"
        return user_id, user_access_token

    username = username.lower()
    username = username.strip()
    display_name = display_name.strip()
    email = email.lower()
    email = email.strip()

    if len(password) < 6:
        raise Problem(status=400, content="Please enter a longer password")

    if len(password) > 30:
        raise Problem(status=400, content="Your password is over 30 characters. Please enter a shorter password")

    if(is_email(email) is False or email.isspace()):
        raise Problem(status=400, content="Please enter a valid email")

    result = get_firebase_user_by_email(email)

    if(result is not None):
        raise Problem(status=400, content="An account with this email already exists")
    
    email_domain = get_email_domain(email)
    
    if(email_domain is None):
        raise Problem(status=400, content="An email domain was not provided")
    
    school_entity = await get_school_entity_by_email_domain(email_domain)

    if(school_entity is None):
        raise Problem(status=400, content="Where2Be does not support your university yet!")

    school_id = school_entity['school_id']

    result = await get_user_entity_by_username(username)
    if(result is not None):
        raise Problem(status=400, content="An account with this username already exists")

    is_verified_org = False
    is_admin = False

    # Create user in the database.
    user_access_token, user_id = await create_user_entity(display_name, username, school_id, is_verified_org, is_admin)

    # Create user in firebase
    result = create_user_firebase(user_id, email, password)

    return user_id, user_access_token