from common.neo4j.moment_neo4j import get_neo4j_session, parse_neo4j_data, run_neo4j_query
from common.s3.moment_s3 import get_bucket_url
from common.models import Problem
from dateutil import parser
import secrets
import random

async def add_push_token(user_id: str, push_token: str, push_type: str):

    await run_neo4j_query("""MATCH (u:User {UserID: $user_id})
        SET u.PushTokens = CASE
        WHEN u.PushTokens IS NULL THEN [ $push_token ]
        WHEN NOT $push_token IN u.PushTokens THEN u.PushTokens + $push_token
        ELSE u.PushTokens
        END""", 
        parameters={
            "user_id": user_id,
            "push_token": push_token
        })

    return 0


async def remove_push_token(user_id: str, push_token: str, push_type: str):

    await run_neo4j_query("""MATCH (u:User {UserID: $user_id})
            WHERE u.PushTokens IS NOT NULL AND ANY(s in u.PushTokens WHERE s = $push_token)
            SET u.PushTokens = [x IN u.PushTokens WHERE x <> $push_token]""", 
            parameters={
            "user_id": user_id,
            "push_token": push_token
        })
    
    return 0

async def get_all_school_users_push_tokens(school_id: str):
    query = """
    MATCH (u:User)-[:user_school]->(school:School{SchoolID: $school_id})
    UNWIND u.PushTokens AS pushTokensList
    RETURN COLLECT({token: pushTokensList, user_id: u.UserID}) AS allPushTokens
    """
    parameters = {
        "school_id": school_id
    }

    result = await run_neo4j_query(query, parameters)

    record = parse_neo4j_data(result, 'single')
    if record is not None:
        return record
    else:
        return None

async def get_all_follower_push_tokens(user_id: str):
    query = """
    MATCH (u:User{UserID: $user_id})<-[:user_follow]-(follower:User)
    WHERE follower.DoNotifyFollowing IS NULL OR follower.DoNotifyFollowing = true
    UNWIND follower.PushTokens AS pushTokensList
    RETURN COLLECT({token: pushTokensList, user_id: follower.UserID}) AS allPushTokens
    """
    parameters = {
        "user_id": user_id
    }
    result = await run_neo4j_query(query, parameters)

    record = parse_neo4j_data(result, 'single')
    if record is not None:
        return record
    else:
        return None
        
async def get_all_joined_users_push_tokens(event_id: str):
    query = """
    MATCH (e:Event{EventID: $event_id})<-[:user_join]-(joinedUser:User)
    UNWIND joinedUser.PushTokens AS pushTokensList
    RETURN COLLECT({token: pushTokensList, user_id: joinedUser.UserID}) AS allPushTokens
    """
    parameters = {
        "event_id": event_id
    }

    result = await run_neo4j_query(query, parameters)
    if result is not None:
        return result['allPushTokens']
    else:
        return None
        
async def get_host_push_tokens(event_id: str):
    query = """
    MATCH (e:Event{EventID: $event_id})<-[:user_host]-(host:User)
    UNWIND host.PushTokens AS pushTokensList
    RETURN COLLECT({token: pushTokensList, user_id: joinedUser.UserID}) AS allPushTokens
    """
    parameters = {
        "event_id": event_id
    }

    result = await run_neo4j_query(query, parameters)

    record = parse_neo4j_data(result, 'single')

    if record is not None:
        return record
    else:
        return None
        
async def get_notification_preferences(user_id: str):
    preferences = {
        "DoNotifyFollowing": False
    }

    query = """
    MATCH (u:User{UserID: $user_id})
    RETURN COALESCE(u.DoNotifyFollowing, true) AS DoNotifyFollowing
    """
    parameters = {
        "user_id": user_id
    }

    result = await run_neo4j_query(query, parameters)

    record = parse_neo4j_data(result, 'single')

    if record is None:
        return None
    else:
        preferences["DoNotifyFollowing"] = record
        return preferences
        


async def set_notification_preferences(user_id: str, preferences: dict):


    permitted_keys = ["DoNotifyFollowing"]

    if any(key not in permitted_keys or not isinstance(value, bool) for key, value in preferences.items()):
        print("INVALID KEY IN SET_NOTIFICATION_PREFERENCES")
        return False

    query = """
    MATCH (u:User{UserID: $user_id})
    SET u += $properties
    RETURN u
    """
    parameters = {
        "user_id": user_id,
        "properties": preferences
    }

    result = await run_neo4j_query(query, parameters)
    if result is None:
        return None
    else:
        return result