import string
import datetime
import pytz
import requests
from timezonefinder import TimezoneFinder
import json

api = 'https://api.where2be.app/'
ver = 'v1.0.1/'
api_url = api + ver

scraper_token = "PLSDKELfSFLKSDJHJHlkjvblkbjfwlj2rieior7y33r20394t0911dqd97q098hbfahfbiafhasldjvLKJHQQPPROOLKLAKSLKQQWIWWIEII222222222238492"


def create_scraper_account(username: string,
                           display_name: string,
                           school_id: string,
                           base64_image: string):
    try:
        assert all((username,
                    display_name,
                    school_id))
    except AssertionError:
        print("One or more parameters are missing in create_scraper_account()!")
        return

    print("Creating scraper account for ", username)

    headers = {'Content-Type': 'application/json'}
    data = {
        'username': username,
        'display_name': display_name,
        'school_id': school_id,
        'scraper_token': scraper_token,
        'picture': base64_image
    }
    response = requests.post(
        api_url + 'auth/create_scraper_account', headers=headers, json=data)

    if response.ok is False:
        print("Error in creating a scraper account with username " + username + "\"!")
        print(str(response.status_code) + ": " + str(response.content))
        exit(1)

    response_json = response.json()

    print("Successfully created scraper account", username, "!\n\n")
    print("UserID: [", response_json['user_id'], "]")
    print("UserAccessToken: [", response_json['user_access_token'], "]")

    if (not response_json['did_change_image']):
        print("\n\nIMPORTANT NOTE: The profile picture wasn't uploaded successfully. You'll need to change it in the app")

    return response_json['user_id'], response_json['user_access_token']


def post_event(user_access_token: string,
               title: string,
               description: string,
               base64_image: string,
               start_date_time: datetime,
               end_date_time: datetime,
               location: string,
               visibility: string,
               interest_ids: list,
               signup_link: str):

    print("Attempting to post event titled \n\"" + title + "\"")
    try:
        assert all((user_access_token,
                    title,
                    description,
                    base64_image,
                    start_date_time,
                    location,
                    visibility,
                    interest_ids))
    except AssertionError:
        print("One or more parameters are missing in post_event()!")
        return

    # get school time zone from user access token
    response = requests.get(
        api_url + 'school/user_access_token/' + user_access_token)

    if response.ok is False:
        print("Error in getting timezone for school paired with event titled \n\"" + title + "\"!")
        print(str(response.status_code) + ": " + str(response.content))
        exit(1)

    response_json = response.json()

    latitude = response_json['latitude']
    longitude = response_json['longitude']

    print("Successfully pulled latitude and longitude of user's school")

    timezone = get_timezone(latitude, longitude)

    print("Timezone: " + str(timezone))
    # convert start_date_time to utc timezone
    converted_start_date_time = convert_time(start_date_time, timezone)

    iso_end_date_time = None
    try:
        converted_end_date_time = convert_time(end_date_time, timezone)
        iso_end_date_time = converted_end_date_time.strftime(
            '%Y-%m-%dT%H:%M:%SZ')
    except:
        print("Could not parse end date time. Uploading without end date time...")

    iso_start_date_time = converted_start_date_time.strftime(
        '%Y-%m-%dT%H:%M:%SZ')

    json_interest_ids = "["

    for interest_id in interest_ids:
        json_interest_ids = json_interest_ids + "\"" + interest_id + "\","

    json_interest_ids = json_interest_ids[:len(json_interest_ids) - 1] + "]"

    print("About to post event to API")

    headers = {'Content-Type': 'application/json'}
    data = {'user_access_token': user_access_token,
            'title': title,
            'description': description,
            'picture': base64_image,
            'start_date_time': iso_start_date_time,
            'end_date_time': iso_end_date_time,
            'location': location,
            'visibility': visibility,
            'interest_ids': json_interest_ids,
            'scraper_token': scraper_token,
            'signup_link': signup_link}

    response = requests.post(
        api_url + 'event/create_event', headers=headers, json=data)

    # Check if the response contains the specific error
    if response.status_code == 400 and response.content == b'This event cannot be in the past':
        print("Warning: Event cannot be in the past for event titled \n\"" +
              title + "\". Skipping...")
        return None

    if response.ok is False:
        print("Error in posting event titled \n\"" + title + "\"!")
        print(str(response.status_code) + ": " + str(response.content))
        exit(1)

    response_json = response.json()
    print("\nSuccessfully created event for event titled \n\"" + title + "\"!")
    print("\nEventID is " + str(response_json['event_id']) + "\n")
    return response_json['event_id']


def get_timezone(latitude, longitude):
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=longitude, lat=latitude)
    return timezone_str


def convert_time(unconverted_time: datetime, timezone: string) -> datetime:

    # ca_tz = pytz.timezone("America/Los_Angeles")
    tz = pytz.timezone(timezone)
    utc_tz = pytz.utc
    dt_lc = tz.localize(unconverted_time)
    dt_utc = dt_lc.astimezone(utc_tz)
    return dt_utc


def get_bucket_url():
    return "https://moment-events.s3.us-east-2.amazonaws.com/"


class Event:
    def __init__(self, user_access_token: str, title: str, description: str, base64_image: str,
                 start_date_time: datetime, end_date_time: datetime, location: str,
                 visibility: str, interest_ids: list):

        self.user_access_token = user_access_token
        self.title = title
        self.description = description
        self.base64_image = base64_image
        self.start_date_time = start_date_time
        self.end_date_time = end_date_time
        self.location = location
        self.visibility = visibility
        self.interest_ids = interest_ids

    def post_event(self):

        print("Attempting to post event titled \n\"" + self.title + "\"")
        try:
            assert all((self.user_access_token,
                        self.title,
                        self.description,
                        self.base64_image,
                        self.start_date_time,
                        self.location,
                        self.visibility,
                        self.interest_ids))
        except AssertionError:
            print("One or more parameters are missing in post_event()!")
            return None

        api = 'https://api.momentevents.app/'
        ver = 'api_ver_1.0.0/'
        api_url = api + ver

        # get school time zone from user access token
        response = requests.get(
            api_url + 'school/user_access_token/' + self.user_access_token)

        if response.ok is False:
            print(
                "Error in getting timezone for school paired with event titled \n\"" + self.title + "\"!")
            print(str(response.status_code) + ": " + str(response.content))
            return None

        response_json = response.json()

        latitude = response_json['latitude']
        longitude = response_json['longitude']

        print("Successfully pulled latitude and longitude of user's school")

        timezone = get_timezone(longitude, latitude)

        print("Timezone: " + str(timezone))
        # convert start_date_time to utc timezone
        converted_start_date_time = convert_time(
            self.start_date_time, timezone)

        iso_end_date_time = None
        try:
            converted_end_date_time = convert_time(
                self.end_date_time, timezone)
            iso_end_date_time = converted_end_date_time.strftime(
                '%Y-%m-%dT%H:%M:%SZ')
        except:
            print("Could not parse end date time. Uploading without end date time...")

        iso_start_date_time = converted_start_date_time.strftime(
            '%Y-%m-%dT%H:%M:%SZ')

        json_interest_ids = "["

        for interest_id in self.interest_ids:
            json_interest_ids = json_interest_ids + "\"" + interest_id + "\","

        json_interest_ids = json_interest_ids[:len(
            json_interest_ids) - 1] + "]"

        print("About to post event to API")

        headers = {'Content-Type': 'application/json'}
        data = {'user_access_token': self.user_access_token,
                'title': self.title,
                'description': self.description,
                'picture': self.base64_image,
                'start_date_time': iso_start_date_time,
                'end_date_time': iso_end_date_time,
                'location': self.location,
                'visibility': self.visibility,
                'interest_ids': json_interest_ids}

        response = requests.post(
            api_url + 'event/create_event', headers=headers, json=data)

        if response.ok is False:
            print("Error in posting event titled \n\"" + self.title + "\"!")
            print(str(response.status_code) + ": " + str(response.content))
            return None

        response_json = response.json()
        print("Successfully created event for event titled \n\"" + self.title + "\"!")
        print("EventID is " + str(response_json['event_id']) + "\n\n\n")
        return response_json['event_id']
