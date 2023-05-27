import boto3
import os

# Creating Session With Boto3.
SES_CLIENT = boto3.client('ses',
                          aws_access_key_id=os.environ.get('SES_ACCESS_KEY'),
                          aws_secret_access_key=os.environ.get('SES_SECRET_ACCESS_KEY'),
                          region_name=os.environ.get('SES_REGION'))

SENDER_EMAIL = 'noreply@momentevents.app'

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
