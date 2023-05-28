import boto3
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

# Creating Session With Boto3.
SES_CLIENT = boto3.client('ses',
                          aws_access_key_id=os.environ.get('SES_ACCESS_KEY'),
                          aws_secret_access_key=os.environ.get('SES_SECRET_ACCESS_KEY'),
                          region_name=os.environ.get('SES_REGION'))

SENDER_EMAIL = 'noreply@momentevents.app'

IS_PROD = os.environ.get('IS_PROD')

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


def send_push_token(expo_token, message, extra):
    session = requests.Session()
    session.headers.update(
        {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate",
            "content-type": "application/json"
        }
    )
    
    try:
        response = PushClient(session=session).publish(
            PushMessage(to=expo_token,
                        body=message,
                        data=extra))
    except PushServerError as exc:
        # Encountered some likely formatting/validation error.
        raise
    except (ConnectionError, HTTPError) as exc:
        # Encountered some Connection or HTTP error - retry a few times in
        # case it is transient.
        raise self.retry(exc=exc)
    try:
        # We got a response back, but we don't know whether it's an error yet.
        # This call raises errors so we can handle them with normal exception
        # flows.
        response.validate_response()
    except DeviceNotRegisteredError:
        # Mark the push token as inactive
        raise
    except PushTicketError as exc:
        # Encountered some other per-notification error.
        raise self.retry(exc=exc)
    