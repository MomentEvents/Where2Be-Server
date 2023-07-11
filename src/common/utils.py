import boto3
from common.neo4j.commands.notificationcommands import remove_push_token
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

from common.constants import IS_PROD

SES_CLIENT = boto3.client('ses',
                          aws_access_key_id=os.environ.get('SES_ACCESS_KEY'),
                          aws_secret_access_key=os.environ.get('SES_SECRET_ACCESS_KEY'),
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

            response = PushClient(session=session).publish(PushMessage(**params))
            
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

    

def send_and_validate_expo_push_notifications(tokens_with_user_id: "set[dict[str, str]]", title: str, message: str, extra):
    # input = {{
    #     "user_id": "blah",
    #     "token": "blah2",
    # }}
    for token_with_user_id in tokens_with_user_id:
        if(not _send_push_token(token_with_user_id["token"], title, message, extra)):
            remove_push_token(token_with_user_id["user_id"], token_with_user_id["token"], "Expo")


def is_email(string):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, string) is not None