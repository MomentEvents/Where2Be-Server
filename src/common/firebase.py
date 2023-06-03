import requests
import json
import firebase_admin
from firebase_admin import auth
import re
import os

from common.models import Problem
from common.utils import send_email

API_KEY = os.environ.get('FIREBASE_API_KEY')
cred = firebase_admin.credentials.Certificate(json.loads(os.environ.get('FIREBASE_CREDENTIALS')))
firebase_admin.initialize_app(cred)

def login_user_firebase(email, password):
    url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=" + API_KEY
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
    return response.json()

def create_user_firebase(user_id, email, password):

    try:
        user = auth.create_user(
            uid=user_id,
            email=email,
            password=password
        )
        return user
    except Exception as e:
        # Handle any errors that occur during the creation
        raise Problem(status=400, content="Error creating user: " + str(e))


def get_firebase_user_by_uid(uid):
    try:
        user = auth.get_user(uid)
        return user
    except Exception as e:
        # Handle any errors that occur during the retrieval
        return None

def get_firebase_user_by_email(email):
    try:
        user = auth.get_user_by_email(email)
        return user
    except Exception as e:
        # Handle any errors that occur during the retrieval
        return None

def change_user_email(uid, new_email):
    try:
        user = auth.update_user(
            uid,
            email=new_email
        )
        print("User email successfully updated.")
        print("New email:", user.email)
    except Exception as e:
        # Handle any errors that occur during the email update
        raise Problem(status=400, content="Error updating user email: " + str(e))

def send_password_reset_email(email):
    try:
        reset_link = auth.generate_password_reset_link(email)
        email_message = "To reset your account's password, click on this link: " + reset_link + "\n\nIf you did not intend to do this action, you can ignore this email\n\n\nThe Moment Team\n\nThis email is sent from an unmonitored inbox. For inquiries, contact team@momentevents.app"
        send_email(email, "Reset your Moment password", email_message)
    except Exception as e:
        # Handle any errors that occur during the email update
        raise Problem(status=400, content="Error generating password reset link: " + str(e))

def send_verification_email(email):
    try:
        verification_link = auth.generate_email_verification_link(email)
        email_message = "Welcome to Moment! We hope you enjoy it here.\n\nTo verify your email, click on this link: " + verification_link + "\n\n\nThe Moment Team\n\nThis email is sent from an unmonitored inbox. For inquiries, contact team@momentevents.app"
        send_email(email, "Verify your Moment account", email_message)
    except Exception as e:
        # Handle any errors that occur during the email update
        raise Problem(status=400, content="Error generating verification email link: " + str(e))