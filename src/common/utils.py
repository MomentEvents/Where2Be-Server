import base64
import boto3
from common.neo4j.commands.notificationcommands import remove_push_token
from common.neo4j.commands.eventcommands import user_isnotified
from common.neo4j.moment_neo4j import run_neo4j_query
from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)
import os
import requests
from requests.exceptions import ConnectionError, HTTPError
import re
import asyncio

from common.constants import IS_PROD
from datetime import datetime, timezone
import json
from dateutil import parser

from better_profanity import profanity

import base64
from PIL import Image
import json
from io import BytesIO
import io


# remove this
import time

from dotenv import load_dotenv

# Load .env file
load_dotenv()

SES_CLIENT = boto3.client('ses',
                          aws_access_key_id=os.environ.get('SES_ACCESS_KEY'),
                          aws_secret_access_key=os.environ.get(
                              'SES_SECRET_ACCESS_KEY'),
                          region_name=os.environ.get('SES_REGION'))

SENDER_EMAIL = 'where2be-team@where2be.app'


def send_email(recipient_email, subject, body):
    response = SES_CLIENT.send_email(
        Source=SENDER_EMAIL,
        Destination={'ToAddresses': [recipient_email]},
        Message={
            'Subject': {'Data': subject},
            'Body': {'Text': {'Data': body}}
        }
    )

    return response


def _send_push_token(expo_token: str, title: str, message: str, extra) -> bool:

    attempts = 0
    max_attempts = 10

    session = requests.Session()
    session.headers.update(
        {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate",
            "content-type": "application/json"
        }
    )
    while attempts < max_attempts:
        try:
            print("Attempt " + str(attempts) + "/" + str(max_attempts))

            # Create parameters dictionary
            params = {"to": expo_token, "body": message, "data": extra}
            # Conditionally add title if it is not None
            if title is not None:
                params["title"] = title

            response = PushClient(session=session).publish(
                PushMessage(**params))

        except PushServerError as exc:
            # Encountered some likely formatting/validation error.
            raise
        except (ConnectionError, HTTPError) as exc:
            # Encountered some Connection or HTTP error - retry a few times in
            # case it is transient.
            print("ENCOUNTERED CONNECTIONERROR OR HTTPERROR \n\n" + str(exc))
            attempts += 1
            continue
        try:
            # We got a response back, but we don't know whether it's an error yet.
            # This call raises errors so we can handle them with normal exception
            # flows.
            response.validate_response()

            return True
        except DeviceNotRegisteredError:
            # Mark the push token as inactive
            return False
        except PushTicketError as exc:
            # Encountered some other per-notification error.

            print("PUSH TICKET ERROR \n\n" + str(exc))
            attempts += 1
            continue

    print("FATAL ERROR: DID NOT SEND PUSH NOTIFICATION")
    return True


async def send_and_validate_expo_push_notifications(tokens_with_user_id: "set[dict[str, str]]", title: str, message: str, extra, isnotified=False):
    # input = {{
    #     "user_id": "blah",
    #     "token": "blah2",
    # }}
    for token_with_user_id in tokens_with_user_id:
        if (not _send_push_token(token_with_user_id["token"], title, message, extra)):
            remove_push_token(
                token_with_user_id["user_id"], token_with_user_id["token"], "Expo")
        elif isnotified:
            await user_isnotified(
                token_with_user_id["user_id"], extra["event_id"])
    print(tokens_with_user_id, " WITH TITLE ",
          title, " WITH MESSAGE ", message)


def store_runtime(run_type: str):

    print("storing time")

    # Store the runtime of the run_type from the worker
    task_info_path = "./worker/task_info.json"

    current_time = datetime.now()

    with open(task_info_path, 'r') as json_file:
        data = json.load(json_file)

    # Update the last run time for the given run_type
    data[run_type] = current_time.isoformat()

    # Write the updated data back to the JSON file
    with open(task_info_path, 'w') as json_file:
        json.dump(data, json_file)


def is_email(string):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, string) is not None


def contains_url(string):

    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    if (len(url) > 0):
        return True

    string_list = string.split()

    regex = r"(?i)\b((?:.com$|.org$|.edu$))"

    for test_string in string_list:
        url = re.findall(regex, test_string)
        if (len(url) > 0):
            return True

    return False


def contains_profanity(string):
    return profanity.contains_profanity(string)


def get_email_domain(email):
    try:
        # Split by '@' and get the domain part
        domain = email.split('@')[1]
        return domain
    except IndexError:
        return None


def validate_username(username):
    # This pattern allows for a-z, A-Z, 0-9, underscore, and hyphen, with no specific length limit.
    pattern = r'^[a-zA-Z0-9_-]*$'
    match = re.match(pattern, username)

    # Return True if the username is valid, False otherwise.
    return match is not None


async def is_event_formatted_correctly(title: str, description: str, start_date_time: str, end_date_time: str, location: str, visibility: str, interest_ids: "list[str]"):
    if (title.isprintable() is False) or (title.isspace() is True):
        return False, "Title is not printable"

    if (len(title) > 70):
        return False, "Title cannot be over 70 characters"

    if (len(title) < 5):
        return False, "Title cannot be under 5 characters"

    if (contains_profanity(title)):
        return False, "We detected profanity in your title. Please change it"

    if (contains_url(title)):
        return False, "Title cannot contain a url"

    if (description.isspace()):
        return False, "Description is not readable"

    if (len(description) > 2000):
        return False, "Description cannot be over 2000 characters"

    if (len(description) < 10):
        return False, "Description cannot be under 10 characters"

    # if (contains_profanity(description)):
    #     return False, "We detected profanity in your description. Please change it"

    try:
        start_date_time_test = parser.parse(start_date_time)
    except:
        return False, "Could not parse start date"

    if end_date_time != None:
        try:
            end_date_time_test = parser.parse(end_date_time)
            if start_date_time_test >= end_date_time_test:
                return False, "Start date cannot be equal to or after end date"
        except:
            return False, "Could not parse end date"

    if start_date_time_test < datetime.now(timezone.utc):
        return False, "This event cannot be in the past"

    if (location.isprintable() is False) or (location.isspace() is True):
        return False, "Location is not printable"

    if (len(location) > 200):
        return False, "Location cannot be over 200 characters"

    if (len(location) < 5):
        return False, "Location cannot be under 5 characters"

    # if (contains_profanity(location)):
    #     return False, "We detected profanity in your location. Please change it"

    if len(interest_ids) != 1:
        return False, "Must only put in one interest tag"

    if (visibility != "Public" and visibility != "Private"):
        return False, "Visibility must be either \"Public\" or \"Private\""

    result = await run_neo4j_query(
        """UNWIND $interest_ids as interest_id
            MATCH (interests:Interest {InterestID: interest_id})
            RETURN interests""",
        parameters={
            "interest_ids": interest_ids,
        },
    )

    # this code sucks
    num_interests = 0
    for record in result:
        num_interests = num_interests + 1

    if num_interests != len(interest_ids):
        return False, "One or more interests do not exist"

    return True, "Event is formatted correctly"


def is_user_formatted_correctly(display_name: str, username: str):
    if len(display_name) > 30:
        return False, "Display name cannot exceed 30 characters"

    if len(display_name) < 3:
        return False, "Display name cannot be below 3 characters"

    if (display_name.isprintable() is False) or (display_name.isspace() is True):
        return False, "Display name is not readable"

    if (contains_url(display_name)):
        return False, "Display name cannot contain a url"

    if (contains_profanity(display_name)):
        return False, "We detected profanity in your display name. Please change it"

    if len(username) > 30:
        return False, "Username cannot exceed 30 characters"

    if len(username) < 6:
        return False, "Username cannot be under 6 characters"

    if validate_username(username) is False:
        return False, "Usernames must only contain a-z, A-Z, 0-9, underscores, or hyphens"

    if (contains_profanity(username)):
        return False, "We detected profanity in your username. Please change it"

    if (contains_url(username)):
        return False, "Username cannot contain a url"

    return True, "User is formatted correctly"


async def is_picture_formatted_correctly(picture):

    try:
        image_bytes = base64.b64decode(picture)
        img = Image.open(io.BytesIO(image_bytes))
    except:
        return False, "Picture is not a valid base64 image"

    return True, "Picture is formatted correctly"
