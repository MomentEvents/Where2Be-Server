from common.neo4j.moment_neo4j import get_neo4j_session
from common.s3.moment_s3 import get_bucket_url
from common.models import Problem
from dateutil import parser
import secrets
import random

def add_push_token(user_id: str, push_token: str, push_type: str):
    
    with get_neo4j_session() as session:
        session.run("""MATCH (u:User {UserID: $user_id})
            SET u.PushTokens = CASE
            WHEN NOT EXISTS(u.PushTokens) THEN [ $push_token ]
            WHEN NOT $push_token IN u.PushTokens THEN u.PushTokens + $push_token
            ELSE u.PushTokens
            END""", 
            parameters={
                "user_id": user_id,
                "push_token": push_token
            })
    
    return 0


def remove_push_token(user_id: str, push_token: str, push_type: str):
    
    with get_neo4j_session() as session:
        session.run("""MATCH (u:User {UserID: $user_id})
                WHERE EXISTS(u.PushTokens) AND ANY(s in u.PushTokens WHERE s = $push_token)
                SET u.PushTokens = [x IN u.PushTokens WHERE x <> $push_token]""", 
                parameters={
                "user_id": user_id,
                "push_token": push_token
            })
    
    return 0

def get_all_follower_push_tokens(user_id: str):
    query = """
    MATCH (u:User{UserID: $user_id})<-[:user_follow]-(follower:User)
    WHERE NOT exists(follower.DoNotifyFollowing) OR follower.DoNotifyFollowing = true
    UNWIND follower.PushTokens AS pushTokensList
    RETURN COLLECT({token: pushTokensList, user_id: follower.UserID}) AS allPushTokens
    """
    parameters = {
        "user_id": user_id
    }

    with get_neo4j_session() as session:
        result = session.run(query, parameters)
        # Assuming you have only one record returned
        record = result.single()
        if record is not None:
            return record['allPushTokens']
        else:
            return None
        
def get_all_joins_and_host_push_tokens(event_id: str):
    query = """
    MATCH (e:Event{EventID: $event_id})<-[:user_join]-(joinedUser:User)
    UNWIND joinedUser.PushTokens AS pushTokensList
    WITH e, COLLECT({token: pushTokensList, user_id: joinedUser.UserID}) AS joinedUserPushTokens
    MATCH (e)<-[:user_host]-(host:User)
    UNWIND host.PushTokens AS pushTokensList
    RETURN joinedUserPushTokens, COLLECT({token: pushTokensList, user_id: host.UserID}) AS hostPushTokens
    """
    parameters = {
        "event_id": event_id
    }

    with get_neo4j_session() as session:
        result = session.run(query, parameters)
        record = result.single()
        if record is not None:
            return {
                "joinedUserPushTokens": record['joinedUserPushTokens'],
                "hostPushTokens": record['hostPushTokens']
            }
        else:
            return None
        
def get_notification_preferences(user_id: str):
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

    with get_neo4j_session() as session:
        result = session.run(query, parameters)
        record = result.single()
        if record is None:
            return None
        else:
            preferences["DoNotifyFollowing"] = record["DoNotifyFollowing"]
            return preferences
        


def set_notification_preferences(user_id: str, preferences: dict):


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

    with get_neo4j_session() as session:
        result = session.run(query, parameters)
        record = result.single()
        if record is None:
            return None
        else:
            return record["u"]