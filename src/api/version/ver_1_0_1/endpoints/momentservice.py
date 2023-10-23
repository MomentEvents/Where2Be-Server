from inspect import Parameter

from markupsafe import string
from common.firebase import create_firestore_document, create_firestore_event_message, delete_firestore_event_message, get_firebase_user_by_uid, get_firestore_document, send_verification_email
from common.models import Problem
from common.neo4j.commands.eventcommands import create_event_entity, get_event_entity_by_event_id
from common.neo4j.commands.notificationcommands import get_all_follower_push_tokens, get_all_joined_users_push_tokens
from common.neo4j.commands.usercommands import get_user_entity_by_user_access_token, get_user_entity_by_user_id
from common.neo4j.converters import convert_moment_entity_to_moment
from common.utils import send_and_validate_expo_push_notifications
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.background import BackgroundTasks
import time




# from datetime import datetime
from dateutil import parser
import bcrypt
import secrets
import random

from common.neo4j.moment_neo4j import parse_neo4j_data, run_neo4j_query
from api.version.ver_1_0_1.auth import is_real_user, is_requester_privileged_for_event, is_requester_privileged_for_user, is_event_formatted, is_real_event, is_picture_formatted, is_valid_user_access_token
from api.helpers import parse_request_data

from common.s3.moment_s3 import upload_base64_image


import platform

from io import BytesIO
import io

import boto3

import base64
from PIL import Image
import json
import cv2
import numpy as np
from common.constants import IS_PROD, SCRAPER_TOKEN, ENABLE_FIREBASE



async def get_home_moments(request: Request) -> JSONResponse:
    """
    Description: Gets moments with an user_id of {user_id}. We send a user_access_token to verify that the user has authorization to view the event (if it is private or not). If it is private, it is only viewable when the user_access_token is the owner of the event.

    params:
        user_access_token: string

    return:
        event_ids: string[],
        events: {
            {$event_id}: {
                host_username: string,
                host_picture: string,
                moments: [
                    {
                        moment_picture: string,
                        type: string,
                        finish: number,
                        viewed: boolean,
                    }
                ]
            }
        },
    """

    user_id = request.path_params["user_id"]

    body = await request.json()

    user_access_token = body.get("user_access_token")

    result = await run_neo4j_query(
        """
        MATCH (u:User{UserAccessToken: $user_access_token})
        CALL {
        
        WITH u
        MATCH (u)-[:user_join|user_host]->(e:Event)
        WITH e
        MATCH (e)-[:moment_event]-(m:Moment), (e)-[:user_host]-(host:User)
        WITH e, host, m
        MATCH (m)-[:moment_user]-(uploader:User)
        WHERE  e.EndDateTime > datetime()
        WITH collect({
            EventID: e.EventID,
            EventPicture: e.Picture,
            HostPicture: host.Picture,
            UploaderID: uploader.UserID,
            UploaderDisplayName: uploader.DisplayName,
            UploaderPicture: uploader.Picture,
            MomentID: m.MomentID,
            MomentPicture: m.Picture,
            Type: m.Type,
            PostedDateTime: m.TimeCreated
            }) AS moment_data
        UNWIND moment_data as results
        RETURN results
        
        UNION

        WITH u
        MATCH (u)-[:user_follow]->(host:User)
        WITH host
        MATCH (e:Event)-[:user_host]-(host), (e)-[:moment_event]-(m:Moment)
        WITH e, host, m
        MATCH (m)-[:moment_user]-(uploader:User)
        WHERE  e.EndDateTime > datetime()
        WITH collect({
            EventID: e.EventID,
            EventPicture: e.Picture,
            HostPicture: host.Picture,
            UploaderID: uploader.UserID,
            UploaderDisplayName: uploader.DisplayName,
            UploaderPicture: uploader.Picture,
            MomentID: m.MomentID,
            MomentPicture: m.Picture,
            Type: m.Type,
            PostedDateTime: m.TimeCreated
            }) AS moment_data
        UNWIND moment_data as results
        RETURN results
        }
        RETURN results
        ORDER BY results.PostedDateTime
        """,
        parameters={
            "user_access_token": user_access_token,
        }
    )

    moment_results = {}
    event_ids = []

    for record in result:
        row = record['results']
        event_id = row['EventID']
        if event_id not in moment_results:
            event_ids.append(event_id)
            event_picture = row['EventPicture']
            host_picture = row['HostPicture']
            moment_results[event_id] = {
                'event_picture': event_picture,
                'host_picture': host_picture,
                'moments': [],
                'visible': False,
            }
        if row['UploaderID'] == user_id:
            moment_results[event_id]['visible'] = True
        moment_data = convert_moment_entity_to_moment(row)
        moment_results[event_id]['moments'].append(moment_data)

    final_results = {
        'event_ids': event_ids,
        'events': moment_results
    }

    return JSONResponse(final_results)


routes = [
    Route("/moments/home/user_id/{user_id}",
        get_home_moments,
        methods=["POST"],
    ),
    
]