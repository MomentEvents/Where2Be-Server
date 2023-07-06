from common.neo4j.moment_neo4j import get_neo4j_session
from common.s3.moment_s3 import get_bucket_url
from common.models import Problem
from dateutil import parser
import secrets
import random

def add_push_token(user_id: str, push_token: str, push_type: str):
    
    with get_neo4j_session() as session:
        session.run("""MATCH (u:User {userId: $user_id})
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
        session.run("""MATCH (u:User {userId: $user_id})
                SET u.PushTokens = [pt IN u.PushTokens WHERE pt <> $push_token]""", 
                parameters={
                "user_id": user_id,
                "push_token": push_token
            })
    
    return 0





    