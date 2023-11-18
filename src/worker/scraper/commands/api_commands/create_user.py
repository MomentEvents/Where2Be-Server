import datetime
import pytz
import requests
from dateutil import parser
from .api_connect import create_scraper_account
import asyncio
import base64
import io
import json


def create_scraper_account_and_log(username, display_name, school_id, image_base64):

    print("Inside create_scraper_account_and_log")
    print(username, display_name, school_id)

    user_id = "temp"
    user_access_token = "temp"

    user_id, user_access_token = create_scraper_account(username,
                                                              display_name,
                                                              school_id,
                                                              image_base64)

    return user_id, user_access_token


def create_user(username, display_name, school_id, image_base64):
    # image_base64 = None

    # if (image_path):
    #     # Read the image file as bytes
    #     with open(image_path, 'rb') as f:
    #         image_bytes = f.read()

    #     # Convert the image bytes to a base64 encoded string
    #     image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    return create_scraper_account_and_log(username,
                                          display_name,
                                          school_id,
                                          image_base64)
