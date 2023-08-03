from datetime import datetime, timezone
import requests
import json
import firebase_admin
from firebase_admin import auth, firestore
import re
import os

from common.models import Problem
from common.utils import send_email

from dotenv import load_dotenv

# Load .env file
load_dotenv()

API_KEY = os.environ.get('FIREBASE_API_KEY')
cred = firebase_admin.credentials.Certificate(json.loads(os.environ.get('FIREBASE_CREDENTIALS')))
app = firebase_admin.initialize_app(cred)
db = firestore.client()

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

def change_firebase_user_email(uid, new_email):
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
    
def delete_firebase_user_by_uid(uid):
    try:
        auth.delete_user(uid)
        print("Successfully deleted user")
    except Exception as e:
        # Handle any errors that occur during the email update
        raise Problem(status=400, content="Error deleting firebase user: " + str(e)) 

async def send_password_reset_email(email):
    user = get_firebase_user_by_email(email)
    if(user is None):
        raise Problem(status=400, content="An account with this email does not exist") 

    try:
        reset_link = auth.generate_password_reset_link(email)
        email_message = "Greetings from Where2Be!\n\nWe received a password reset request for the Where2Be account linked to this email. To reset your account's password, click on this link: " + reset_link + "\n\nIf you did not intend to do this action, you can ignore this email.\n\n\nBest,\nThe Where2Be Team\nhttps://where2be.app"
        send_email(email, "Reset your Where2Be password", email_message)
    except Exception as e:
        # Handle any errors that occur during the email update
        raise Problem(status=400, content="Error generating password reset link: " + str(e))

async def send_verification_email(email):
    user = get_firebase_user_by_email(email)
    if(user is None):
        raise Problem(status=400, content="An account with this email does not exist") 
    
    if(user.email_verified is True):
        raise Problem(status=400, content="This account is already verified") 
    
    try:
        verification_link = auth.generate_email_verification_link(email)
        email_message = "Welcome to Where2Be! We hope you enjoy it here.\n\nTo verify your email, click on this link: " + verification_link + "\n\n\nBest,\nThe Where2Be Team\nhttps://where2be.app"
        send_email(email, "Verify your Where2Be account", email_message)
    except Exception as e:
        # Handle any errors that occur during the email update
        raise Problem(status=400, content="Error sending verification email link: " + str(e))
    
def create_firestore_document(collection: str, document: str, data):
    # if document is None, then a randomized id will be assigned
    if document:
        doc_ref = db.collection(collection).document(document)
    else:
        doc_ref = db.collection(collection).document()

    doc_ref.set(data)

    return doc_ref.id

def get_firestore_document(collection: str, document: str):
    doc_ref = db.collection(collection).document(document)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()
    else:
        return None

def delete_firestore_document(collection: str, document: str) -> bool:
    if document:
        db.collection(collection).document(document).delete()
        return True
    else:
        return False

def create_firestore_event_message(event_id: str, user_id: str, message: str):

    data = {
        'user_id': user_id,
        'message': message,
        'timestamp': datetime.now(timezone.utc)
    }

    return create_firestore_document("EVENT_MESSAGES_" + event_id, None, data)

def delete_firestore_event_message(event_id: str, message_id: str):

    # THIS ASSUMES THAT THE USER OWNS THIS MESSAGE AND CAN DELETE IT. THIS IS BECAUSE ONLY HOSTS CAN POST MESSAGES
    return delete_firestore_document("EVENT_MESSAGES_" + event_id, message_id)