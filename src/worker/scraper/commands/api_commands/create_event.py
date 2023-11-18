import datetime
from datetime import datetime
import pytz
import requests
from dateutil import parser
from .api_connect import post_event
import asyncio
import base64
import io
import json


def post_event_and_log(user_access_token, title, description, image_base64, start_date_time, end_date_time, location, visibility, tags, signup_link):
    print("####### posting event")
    event_id = post_event(user_access_token, title, description, image_base64,
                          start_date_time, end_date_time, location, visibility, tags, signup_link)

    # filename = "./created_events.json"

    # # Read the existing data from the file, if it exists
    # try:
    #     with open(filename, 'r') as f:
    #         existing_data = json.load(f)
    # except (FileNotFoundError, json.JSONDecodeError):
    #     existing_data = {}

    # event_data = {
    #     "title": title,
    #     "description": description,
    #     "start_date_time": start_date_time.strftime('%Y-%m-%d %H:%M:%S'),
    #     "end_date_time": end_date_time.strftime('%Y-%m-%d %H:%M:%S'),
    #     "location": location,
    #     "visibility": visibility,
    #     "tag": tags[0],
    #     "date_posted": (datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
    #     "signup_link": signup_link,
    #     "host_user_access_token": user_access_token,
    # }

    # existing_data[event_id] = event_data

    # # Write updated data back to the file
    # with open(filename, 'w') as f:
    #     json.dump(existing_data, f, indent=4)

    # print("This information has been logged into", filename, "\n\n")


def create_event(user_access_token, title, description, location, start_date_time, end_date_time, image_base64, tag="social", signup_link=None):
    # # Read the image file as bytes
    # with open(image_path, 'rb') as f:
    #     image_bytes = f.read()

    # # Convert the image bytes to a base64 encoded string
    # image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    # Input string
    start_date_string = start_date_time

    start_date_time = parser.parse(start_date_string)

    end_date_string = end_date_time

    end_date_time = parser.parse(end_date_string)

    post_event_and_log(user_access_token,
                       title,
                       description,
                       image_base64,
                       start_date_time,
                       end_date_time,
                       location,
                       "Public",
                       [tag],
                       signup_link
                       )
