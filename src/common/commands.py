from common.neo4j.commands import create_user_entity, get_school_entity_by_school_id, get_user_entity_by_username
from common.neo4j.moment_neo4j import get_neo4j_session
from common.models import Problem
from common.utils import is_email
from common.firebase import login_user_firebase, create_user_firebase, get_firebase_user_by_uid, get_firebase_user_by_email, send_verification_email
from common.constants import IS_PROD

def login(usercred: str, password: str):

    if(not IS_PROD):
        user_access_token = None
        user_id = None
        return user_id, user_access_token
    # Check if it's a username or email

    usercred = usercred.lower()
    usercred = usercred.strip()

    email = usercred    
    if(is_email(usercred) is False):

        # Get user by username
        user = get_user_entity_by_username(usercred)

        # If there is no user with the username
        if(user is None):
            raise Problem(status=400, content="An account with this username does not exist")
        
        user_id = user['user_id']

        firebase_user = get_firebase_user_by_uid(user_id)

        if(firebase_user is None):
            raise Problem(status=400, content="This specific account does not have an email linked to it. Please contact support to resolve this issue")
          
        if(firebase_user.email_verified is False):
            raise Problem(status=400, content="You must verify your email before logging in")
        
        email = firebase_user.email
    else:
        # usercred is email
        firebase_user = get_firebase_user_by_email(usercred)

        if (firebase_user is None):
            raise Problem(status=400, content="An account with this email does not exist")
        
        if(firebase_user.email_verified is False):
            raise Problem(status=400, content="You must verify your email before logging in")

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

    with get_neo4j_session() as session:

        result = session.run(
            """MATCH (u:User {UserID: $user_id})
            RETURN u""",
            parameters={
                "user_id": user_id
            },
        )

        record = result.single()

        if(record is None):
            raise Problem(status=400, content="There is no user associated with this returned UserID. Please contact support to resolve this issue")
        
        data = record[0]

        print("user_id ", user_id)
        print("user_access_token ", data['UserAccessToken'])

        return user_id, data['UserAccessToken']
        
def signup(username, display_name, email, password, school_id):
    if(not IS_PROD):
        raise Problem(status=400, content="""Dev mode has been turned on, so signup is disabled. Signup is through Firebase, not on our own systems.
        You can simply just hit the login endpoint and return your own user_access_token from the local database to simulate a login.""")

    username = username.lower()
    username = username.strip()
    display_name = display_name.strip()
    email = email.lower()
    email = email.strip()

    if len(password) < 7:
        raise Problem(status=400, content="Please enter a more complex password")

    if len(password) > 30:
        raise Problem(status=400, content="Your password is over 30 characters. Please enter a shorter password")

    if(is_email(email) is False or email.isspace()):
        raise Problem(status=400, content="Please enter a valid email")

    result = get_firebase_user_by_email(email)
    if(result is not None):
        if(result.email_verified is False):
            send_verification_email(email)
            raise Problem(status=200, content="Re-sent verification email")

        raise Problem(status=400, content="An account with this email already exists")

    result = get_user_entity_by_username(username)
    if(result is not None):
        raise Problem(status=400, content="An account with this username already exists")

    result = get_school_entity_by_school_id(school_id)
    if(result is None):
        raise Problem(status=400, content="School does not exist")


    is_verified_org = False

    # Create user in the database.
    user_access_token, user_id = create_user_entity(display_name, username, school_id, is_verified_org)

    # Create user in firebase
    result = create_user_firebase(user_id, email, password)
    send_verification_email(email)


    return user_access_token