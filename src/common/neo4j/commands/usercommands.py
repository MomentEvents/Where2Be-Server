from common.neo4j.moment_neo4j import parse_neo4j_data, run_neo4j_query
from common.neo4j.converters import convert_user_entity_to_user, convert_school_entity_to_school
from common.s3.moment_s3 import get_bucket_url
from common.models import Problem
from dateutil import parser
import secrets
import random
from datetime import datetime, timezone


async def create_user_entity(display_name: str, username: str, school_id: str, is_verified_org: bool, is_admin: bool, account_type="Person"):
    username = username.lower()
    username = username.strip()
    display_name = display_name.strip()

    random_number = str(random.randint(1, 5))
    default_user_image = (
        get_bucket_url()+"app-uploads/images/users/static/default" + random_number + ".png"
    )

    user_access_token = secrets.token_urlsafe()
    user_id = secrets.token_urlsafe()

    result = await run_neo4j_query(
        """CREATE (u:User {UserID: $user_id, Username: $username, LastUsedName: $last_used_name, LastUsedEmail: $last_used_email, LastUsedPhoneNumber: $last_used_phone_number, LastUsedMajor: $last_used_major, LastUsedYear: $last_used_year, Picture:$picture, DisplayName:$display_name, UserAccessToken:$user_access_token, VerifiedOrganization:$is_verified_org, Administrator:$is_admin, AccountType:$account_type})
        WITH u
        MATCH(n:School{SchoolID: $school_id})
        CREATE (u)-[r:user_school]->(n)
        RETURN u""",
        parameters={
            "username": username,
            "display_name": display_name,
            "last_used_name": display_name,
            "last_used_email": "",
            "last_used_phone_number": "",
            "last_used_major": "",
            "last_used_year": "",
            "picture": default_user_image,
            "school_id": school_id,
            "user_access_token": user_access_token,
            "user_id": user_id,
            "is_verified_org": is_verified_org,
            "is_admin": is_admin,
            "account_type": account_type,
        },
    )

    return user_access_token, user_id


async def get_user_entity_by_username(username: str):

    result = await run_neo4j_query(
        """MATCH (u:User {Username: $username})
        RETURN u""",
        parameters={
            "username": username
        },
    )

    data = parse_neo4j_data(result, 'single')

    if (not data):
        return None

    user = convert_user_entity_to_user(
        data, show_num_events_followers_following=False)

    print(user)

    return user


async def get_user_entity_by_user_id(user_id: str, self_user_access_token: str, show_num_events_followers_following: bool):

    # self_user_access token is used to get UserFollow with show_num_events_followers_following. In other words, both have to exist or neither exist
    parameters = {
        "user_id": user_id
    }

    if (self_user_access_token):
        parameters["user_access_token"] = self_user_access_token

    match_query = """MATCH (u:User {UserID: $user_id}) """

    statistics_query = """WITH u, COUNT{()-[:user_follow]->(u)} as NumFollowers,
            COUNT{()<-[:user_follow]-(u)} as NumFollowing,
            COUNT{(u)-[:user_host]->(:Event)} as NumEvents,"""

    user_follow_query = """EXISTS((u)<-[:user_follow]-(:User{UserAccessToken: $user_access_token})) 
            as UserFollow""" if self_user_access_token is not None else """False as UserFollow"""

    return_query = """
    RETURN {
                UserID: u.UserID,
                DisplayName: u.DisplayName,
                Username: u.Username,
                Picture: u.Picture,
                VerifiedOrganization: u.VerifiedOrganization,
                UserFollow: UserFollow,
                NumFollowers: NumFollowers,
                NumFollowing: NumFollowing,
                NumEvents: NumEvents
            }
    """ if show_num_events_followers_following else """
    RETURN {
                UserID: u.UserID,
                DisplayName: u.DisplayName,
                Username: u.Username,
                Picture: u.Picture,
                VerifiedOrganization: u.VerifiedOrganization
            }
    """

    if (show_num_events_followers_following):
        final_query = match_query + statistics_query + user_follow_query + return_query
    else:
        final_query = match_query + return_query

    print(final_query)

    result = await run_neo4j_query(
        final_query,
        parameters=parameters,
    )

    data = parse_neo4j_data(result, 'single')

    if (not data):
        return None

    user_data = convert_user_entity_to_user(
        data, show_num_events_followers_following)

    return user_data


async def get_user_entity_by_event_id(event_id):

    result = await run_neo4j_query(
        """MATCH (e:Event{EventID : $event_id})<-[:user_host]-(u:User)
    RETURN u""",
        parameters={
            "event_id": event_id,
        },
    )

    data = parse_neo4j_data(result, 'single')

    if (not data):
        return None

    user_data = convert_user_entity_to_user(
        data, show_num_events_followers_following=False)

    return user_data


async def get_user_entity_by_user_access_token(user_access_token: str, show_num_events_followers_following: bool):
    parameters = {
        "user_access_token": user_access_token
    }

    match_query = """MATCH (u:User {UserAccessToken: $user_access_token}) """

    statistics_query = """WITH u, COUNT{()-[:user_follow]->(u)} as NumFollowers,
            COUNT{()<-[:user_follow]-(u)} as NumFollowing,
            COUNT{(u)-[:user_host]->(:Event)} as NumEvents,"""

    user_follow_query = """False as UserFollow"""

    return_query = """
    RETURN {
                UserID: u.UserID,
                DisplayName: u.DisplayName,
                Username: u.Username,
                Picture: u.Picture,
                VerifiedOrganization: u.VerifiedOrganization,
                UserFollow: UserFollow,
                NumFollowers: NumFollowers,
                NumFollowing: NumFollowing,
                NumEvents: NumEvents
            }
    """ if show_num_events_followers_following else """
    RETURN {
                UserID: u.UserID,
                DisplayName: u.DisplayName,
                Username: u.Username,
                Picture: u.Picture,
                VerifiedOrganization: u.VerifiedOrganization
            }
    """

    if (show_num_events_followers_following):
        final_query = match_query + statistics_query + user_follow_query + return_query
    else:
        final_query = match_query + return_query

    result = await run_neo4j_query(
        final_query,
        parameters=parameters,
    )

    data = parse_neo4j_data(result, 'single')

    if (not data):
        return None

    user_data = convert_user_entity_to_user(
        data, show_num_events_followers_following)

    return user_data


async def get_user_prefilled_form_by_user_id(user_id: str):
    result = await run_neo4j_query(
        """ MATCH (u:User {UserID: $user_id}) 
            RETURN {
                UserID: u.UserID,
                LastUsedName: u.LastUsedName,
                LastUsedEmail: u.LastUsedEmail,
                LastUsedPhoneNumber: u.LastUsedPhoneNumber,
                LastUsedMajor: u.LastUsedMajor,
                LastUsedYear: u.LastUsedYear
            } AS result
        """,
        parameters = {
            "user_id": user_id
        }
    )

    data = parse_neo4j_data(result, 'single')

    if (not data):
        return None

    user_data = {
        "user_id": data["UserID"],
        "name": data["LastUsedName"],
        "email": data["LastUsedEmail"],
        "phone_number": data["LastUsedPhoneNumber"],
        "major": data["LastUsedMajor"],
        "year": data["LastUsedYear"],
    }

    return user_data

async def create_follow_connection(from_user_id, to_user_id):
    timestamp = datetime.now(timezone.utc)

    query = """
    MATCH (u1:User{UserID: $from_user_id}),(u2:User{UserID: $to_user_id}) 
    MERGE (u1)-[r:user_follow]->(u2)
    SET r.Timestamp = datetime($timestamp)
    """

    parameters = {
        "from_user_id": from_user_id,
        "to_user_id": to_user_id,
        # Convert DateTime object to ISO 8601 string format
        "timestamp": timestamp.isoformat()
    }

    await run_neo4j_query(query, parameters)

    return 0


async def delete_follow_connection(from_user_id, to_user_id):
    query = """MATCH (u1:User{UserID: $from_user_id})-[r:user_follow]->(u2:User{UserID: $to_user_id})
                        DELETE r"""
    parameters = {
        "from_user_id": from_user_id,
        "to_user_id": to_user_id,
    }

    await run_neo4j_query(query, parameters)

    return 0


async def create_not_interested_connection(user_id, event_id):
    timestamp = datetime.now(timezone.utc)

    query = """
    MATCH (u:User{UserID: $user_id}),(e:Event{EventID: $event_id}) 
    MERGE (u)-[r:user_not_interested]->(e)
    SET r.Timestamp = datetime($timestamp)
    """

    parameters = {
        "user_id": user_id,
        "event_id": event_id,
        # Convert DateTime object to ISO 8601 string format
        "timestamp": timestamp.isoformat()
    }

    await run_neo4j_query(query, parameters)

    return 0


async def delete_not_interested_connection(user_id, event_id):
    query = """MATCH (u:User{UserID: $user_id})-[r:user_not_interested]->(e:Event{EventID: $event_id})
                DELETE r"""

    parameters = {
        "user_id": user_id,
        "event_id": event_id,
    }

    await run_neo4j_query(query, parameters)

    return 0


async def create_viewed_connections(user_id, event_ids):
    timestamp = datetime.now(timezone.utc)

    query = """
    MATCH (u:User {UserID: $user_id})
    UNWIND $event_ids AS eventId
    MATCH (e:Event {EventID: eventId})
    MERGE (u)-[r:user_viewed]->(e)
    ON CREATE SET r.Timestamp = datetime($timestamp)
    """

    parameters = {
        "user_id": user_id,
        "event_ids": event_ids,
        # Convert DateTime object to ISO 8601 string format
        "timestamp": timestamp.isoformat()
    }

    await run_neo4j_query(query, parameters)

    return 0


async def create_join_connection(user_id, event_id):
    timestamp = datetime.now(timezone.utc)

    query = """
    MATCH (u:User{UserID: $user_id}),(e:Event{EventID: $event_id}) 
    MERGE (u)-[r:user_join]->(e)
    SET r.Timestamp = datetime($timestamp),r.IsNotified = False
    """

    parameters = {
        "user_id": user_id,
        "event_id": event_id,
        # Convert DateTime object to ISO 8601 string format
        "timestamp": timestamp.isoformat()
    }

    await run_neo4j_query(query, parameters)

    return 0


async def delete_join_connection(user_id, event_id):
    query = """MATCH (u:User{UserID: $user_id})-[r:user_join]->(e:Event{EventID: $event_id})
                DELETE r"""

    parameters = {
        "user_id": user_id,
        "event_id": event_id,
    }

    await run_neo4j_query(query, parameters)

    return 0


async def create_shoutout_connection(user_id, event_id):
    timestamp = datetime.now(timezone.utc)

    query = """
    MATCH (u:User{UserID: $user_id}),(e:Event{EventID: $event_id}) 
    MERGE (u)-[r:user_shoutout]->(e)
    SET r.Timestamp = datetime($timestamp)
    """

    parameters = {
        "user_id": user_id,
        "event_id": event_id,
        # Convert DateTime object to ISO 8601 string format
        "timestamp": timestamp.isoformat()
    }

    await run_neo4j_query(query, parameters)

    return 0


async def delete_shoutout_connection(user_id, event_id):
    query = """MATCH (u:User{UserID: $user_id})-[r:user_shoutout]->(e:Event{EventID: $event_id})
                DELETE r"""

    parameters = {
        "user_id": user_id,
        "event_id": event_id,
    }

    await run_neo4j_query(query, parameters)

    return 0

###


async def get_all_bots():

    result = await run_neo4j_query("""MATCH (u:User)
                    where u.AccountType = "Bot"
                    RETURN u""")

    bot_array = []
    for record in result:
        if record == None:
            return []
        data = record['u']
        bot_array.append(convert_user_entity_to_user(data))

    return bot_array
