from common.neo4j.moment_neo4j import get_neo4j_session
from common.s3.moment_s3 import get_bucket_url
from common.models import Problem
from dateutil import parser
import secrets
import random

def create_push_token_entity(user_id: str, push_token: str, push_type: str):
    test = 1

    