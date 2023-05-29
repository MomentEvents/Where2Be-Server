import requests
import json
import firebase_admin
from firebase_admin import auth
import re
import os

from common.models import Problem

API_KEY = "AIzaSyAFj_kdZZ8f9VkOb3l-F4alS7Sv2RiYAAo"
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

def send_password_reset_code(email):
    try:
        reset_link = auth.generate_password_reset_link(email)
        print("Password reset email sent successfully.")
        print("Password reset link:", reset_link)
    except Exception as e:
        # Handle any errors that occur during the email update
        raise Problem(status=400, content="Error generating password reset link: " + str(e))

def send_verification_email(uid):
    try:
        auth.send_email_verification(uid)
        print("Verification email sent successfully.")
    except Exception as e:
        # Handle any errors that occur during the email update
        raise Problem(status=400, content="Error generating verification email link: " + str(e))