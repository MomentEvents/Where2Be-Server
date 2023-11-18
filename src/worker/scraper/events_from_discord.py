import requests
import numpy as np
import matplotlib.pyplot as plt

from importlib_metadata import os
# from nbclient import client

import boto3
import os

import pandas as pd

import secrets
import bcrypt

import json
import datetime
from dateutil import parser
from datetime import datetime, timedelta

import re

from transformers import BertTokenizer, AutoTokenizer, BertForTokenClassification
import torch
from collections import Counter

from flair.data import Sentence
from flair.models import SequenceTagger

from neo4j import GraphDatabase

import random
import string

from requests_toolbelt.multipart.encoder import MultipartEncoder

from commands.api_commands.api_connect import get_bucket_url, Event
from commands.api_commands.images import Image
from commands.api_commands.create_user import create_user
from commands.api_commands.create_event import create_event

from commands.s3_commands import get_json_from_s3


productionserver = "https://api.where2be.app"
version = "/api_ver_1.0.0"

momentAPIVersionless = productionserver
momentAPI = momentAPIVersionless + version

os.environ["TRANSFORMERS_CACHE"] = "/app/scraper/cache"


def get_bucket_url():
    return "https://api.where2be.app.s3.us-east-2.amazonaws.com/"


def get_pred_type(prediction):

    if prediction == "O" or prediction == "[PAD]" or prediction == "[SEP]":
        return prediction
    else:
        return prediction.split("-")[1]


def get_vote_type(votes):
    # Since Python 3.7, Counter maintains insertion order.
    # Since we want to preserve the first label in case of ties, we need to reverse the votes,
    # as we previously recorded them backwards.
    votes = [get_pred_type(vote) for vote in reversed(votes)]
    majority = Counter(votes).most_common(1)
    majority_label = majority[0][0]

    return majority_label


def merge_tokens(bpe_text, bpe_predictions, id2label, tokenizer):
    """
    BPEs are merged into single tokens in this step, where corresponding predictions get aggregated
    into a single token by virtue of majority voting.
    Even breaks (e.g., something like "me ##ssa ##ge | B-DATE, O, I-DURATION") will be decided by the first tag result,
    in this case "DATE" because of the tag of "me". If there is no B-tag in the current instance at all,
    the first token still decides. Note that there are no ambiguities about the B/I distinction here, since we only
    look at multi-BPE tokens, and not at tags spanning multiple *full-word* tokens.
    TODO: Note that this function gets rid of the B/I distinction for downstream tasks as well currently!
      This can be changed by not abstracting the vote to the type only, and still carrying the B-/I- prefix with it.
    :param bpe_text:
    :param bpe_predictions:
    :param id2label: Turning predicted ids back to the actual labels
    :param tokenizer: Tokenizer required to translate token ids back to the words themselves.
    :return: List of tuples containing (token, type_label) pairs.
    """
    merged_tokens = []
    prev_multi_instance = False
    current_multi_vote = []
    current_multi_token = ""
    # Iterate in reverse to immediately see when we deal with a multi-BPE instance and start voting
    for token_id, pred_id, in zip(reversed(bpe_text), reversed(bpe_predictions)):
        # print(token_id.numpy())
        token = tokenizer.ids_to_tokens[int(token_id)]

        # print(pred_id)
        pred = id2label[int(pred_id)]

        # Skip special tokens
        if token in ("[PAD]", "[CLS]", "[SEP]"):
            continue

        # Instance for multi-BPE token
        if token.startswith("##"):
            current_multi_token = f"{token[2:]}{current_multi_token}"
            current_multi_vote.append(pred)
        else:
            # Need to merge votes
            if current_multi_token:
                current_multi_token = f"{token}{current_multi_token}"
                current_multi_vote.append(pred)
                merged_tokens.append(
                    (current_multi_token, get_vote_type(current_multi_vote)))
                current_multi_token = ""
                current_multi_vote = []
            # Previous token was single word anyways
            else:
                merged_tokens.append((token, get_pred_type(pred)))

    # Bring back into right order for later processing
    merged_tokens.reverse()
    return merged_tokens


def pred_time(input_text):
    processed_text = tokenizer(input_text, return_tensors="pt")
    result = model(**processed_text)
    classification = result[0]
    labeled_list = merge_tokens(processed_text['input_ids'][0], torch.max(
        classification[0], dim=1)[1], id2label, tokenizer)
    final_list = []
    for word in labeled_list:
        if word[1] != 'O':
            final_list.append(word)
    return final_list


def get_loc(sent):
    if sent == "":
        return []
    sentence = Sentence(sent)
    tagger.predict(sentence)

    location_stack = []

    # print the sentence with all annotations
    # print(sentence)

    sentence_lowercase = sent.lower()

    # print('The following NER tags are found:')

    # iterate over entities and print each
    for entity in sentence.get_spans('ner'):
        label = entity.get_label("ner").value
        if label == 'ORG' or label == 'LOC':
            # print(entity.text)
            if "club" not in entity.text.lower():
                location_stack.append(entity.text)

    loc_index = -1
    if location_stack != []:
        # print("Earliest loc: ",len(sent.split(location_stack[0])[0]))
        loc_index = len(sent.split(location_stack[0])[0])

    if 'zoom' in sentence_lowercase:  # tag it according to its location
        a = re.search(r'\b(zoom)\b', sentence_lowercase)
        # print(a.start())
        if a != None and (a.start() < loc_index or loc_index == -1):
            location_stack.append('Zoom')

    if 'info' in sentence_lowercase:
        location_stack.append('Zoom')

    return location_stack


def lfnc(test_date, weekday_idx): return test_date + \
    timedelta(days=(weekday_idx - test_date.weekday() + 7) % 7)


def lfnc2(test_date, relative_day): return test_date + \
    timedelta(days=relative_day)


def lfnc3(test_date, month, day): return test_date.replace(
    day=day, month=month)


def get_time(message):
    out_list = []

    text = message['content']

    out_list = pred_time(text)

    if out_list == []:
        return []
    # print(out_list)

    time_stack = []
    date_stack = []
    time_of_day = "pm"

    date = datetime.strptime(message['timestamp'][:10], "%Y-%m-%d")

    i = 0
    while i < len(out_list):
        # print(out_list[i])

        if out_list[i][1] == 'TIME':
            flag = 1
            # check am or pm
            if 'pm' in out_list[i][0].lower() or 'am' in out_list[i][0].lower():
                time_of_day = out_list[i][0][-2:]
                flag = 0

            # if its formatted as x:yz
            if out_list[i][0].isnumeric() and i+2 < len(out_list) and int(out_list[i][0]) <= 12:
                # if its formatted as x:yz
                if out_list[i+1][1] == 'TIME' and out_list[i+1][0].strip() == ":":
                    time_stack.append(
                        out_list[i][0]+out_list[i+1][0]+out_list[i+2][0][:2])
                    i = i+2
                    flag = 0
                else:
                    time_stack.append(out_list[i][0])  # if its just x
                    flag = 0

            elif out_list[i][0].lower().replace('pm', '').replace('am', '').isnumeric() and int(out_list[i][0].lower().replace('pm', '').replace('am', '')) <= 12:  # if its just x or x pm/x am
                time_stack.append(out_list[i][0].lower().replace(
                    'pm', '').replace('am', ''))
                flag = 0

            if flag:
                res = -1
                for relative_day in relative_date_list:
                    if relative_day in out_list[i][0].lower():
                        res = lfnc2(date, relative_date_list[relative_day])
                        break
                if res != -1:
                    date_stack.append(str(res.strftime("%Y/%m/%d")))

        if out_list[i][1] == 'DATE' or out_list[i][1] == 'SET':    # if it has a date tag
            res = -1
            flag = 1

            possible_num = out_list[i][0].replace("th", "").replace("rd", "").replace(
                "nd", "").replace("st", "")  # this change was made for insta, reflect on discord
            if possible_num.isnumeric() and i+1 < len(out_list):  # ex: 5 jan
                for month in month_list:
                    if month in out_list[i+1][0].lower() and int(possible_num) < 32:
                        # lfnc3(date, month_list[month], int(out_list[i][0]))
                        res = date.replace(
                            day=int(possible_num), month=month_list[month])
                        flag = 0
                        i = i+1
                        break
                if flag and int(possible_num) < 32:
                    res = date.replace(day=int(possible_num))
                    flag = 0

            if flag:
                for month in month_list:
                    if month in out_list[i][0].lower() and i+1 < len(out_list):  # ex: jan 5
                        possible_num = out_list[i+1][0].replace("th", "").replace(
                            "rd", "").replace("nd", "").replace("st", "")
                        if possible_num.isnumeric() and int(possible_num) < 32:
                            res = date.replace(
                                day=int(possible_num), month=month_list[month])
                            flag = 0
                            i = i+1
                        break

            # if out_list[i][0].isnumeric() and i+1 < len(out_list):  # ex: 5 jan
            #   for month in month_list:
            #     if month in out_list[i+1][0].lower() and int(out_list[i][0]) < 32:
            #       res = date.replace(day=int(out_list[i][0]), month=month_list[month])#lfnc3(date, month_list[month], int(out_list[i][0]))
            #       flag = 0
            #       i=i+1
            #       break
            #   if flag and int(out_list[i][0]) < 32:
            #     res = date.replace(day=int(out_list[i][0]))
            #     flag = 0

            if flag:
                for month in month_list:
                    if month in out_list[i][0].lower() and i+1 < len(out_list):  # ex: jan 5
                        possible_num = out_list[i+1][0].replace("th", "").replace(
                            "rd", "").replace("nd", "").replace("st", "")
                        if possible_num.isnumeric() and int(possible_num) < 32:
                            res = date.replace(
                                day=int(possible_num), month=month_list[month])
                            flag = 0
                            i = i+1
                        break

            if flag:
                for day in day_list:
                    if day in out_list[i][0].lower():
                        res = lfnc(date, day_list[day])
                        flag = 0
                        break

            if flag:
                for relative_day in relative_date_list:
                    if relative_day in out_list[i][0].lower():
                        res = lfnc2(date, relative_date_list[relative_day])
                        flag = 0
                        break

            if res != -1:
                date_stack.append(str(res.strftime("%Y/%m/%d")))

        i += 1

    if time_stack != [] and date_stack != []:
        return {"time_of_day": time_of_day, "time_stack": time_stack, "date_stack": date_stack}

    return []


def get_hash_pwd(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def random_key_given_seed(seed):
    # Set the seed value
    random.seed(seed)

    # Define the possible characters to use in the random string
    possible_chars = string.ascii_letters + string.digits

    # Generate a random 32-character string
    rand_str = ''.join(random.choices(possible_chars, k=8))

    # Print the random string
    return (rand_str)


def read_keys_from_file(filename):
    """Utility function to read keys from a file into a set."""
    with open(filename, 'r') as f:
        return set(f.read().splitlines())


def write_keys_to_file(filename, keys):
    """Utility function to write keys from a set into a file."""
    with open(filename, 'w') as f:
        for key in keys:
            f.write(key + "\n")


def append_to_json_file(file_path, event_dict):
    data = []

    print("IN append_to_json_file ###########")

    # Check if the file exists
    if os.path.exists(file_path):
        print("path exists ###########")
        # Read existing data
        with open(file_path, 'r') as file:
            data = json.load(file)

    # Append new event
    data.append(event_dict)

    print("in append_to_json_file data:", data)

    # Write back to the file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# STARTING RUN


tokenizer = AutoTokenizer.from_pretrained(
    "satyaalmasian/temporal_tagger_BERT_tokenclassifier", use_fast=False)
model = BertForTokenClassification.from_pretrained(
    "satyaalmasian/temporal_tagger_BERT_tokenclassifier")

id2label = {v: k for k, v in model.config.label2id.items()}

print("id2label: ", id2label)

# tagger = SequenceTagger.load(
#     "/home/ec2-user/.flair/models/ner-english-large/07301f59bb8cb113803be316267f06ddf9243cdbba92a4c8067ef92442d2c574.554244d3476d97501a766a98078421817b14654496b86f2f7bd139dc502a4f29")

tagger = SequenceTagger.load("flair/ner-english-large")


print("Downloading complete")

day_list = {"monday": 0, "tuesday": 1, "wednesday": 2,
            "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
month_list = {"jan": 1, "feb": 2, "march": 3, "apr": 4, "may": 5, "june": 6,
              "july": 7, "august": 8, "sept": 9, "october": 10, "nov": 11, "december": 12}
relative_date_list = {"today": 0, "tomorrow": 1, "tonight": 0, "night": 0}


user_list = []


# Step 1 & 2: Read and write back cleaned keys for keys.txt
current_keys = read_keys_from_file('./keys.txt')
write_keys_to_file('./keys.txt', current_keys)

print(current_keys)


user_dict = {}
events_map = {}

just_for_now = {}

with open('Users.json') as json_file:
    user_dict = json.load(json_file)

# with open('Users.json') as json_file:
#     just_for_now = json.load(json_file)

# with open('Events.json') as json_file:
#     events_map = json.load(json_file)

# print("all events: ", events_map)


exception_count = 0
for key_id, key in enumerate(list(current_keys)):
    cnt = 0
    id_extracted_list = []

    # for dirname, dirs, files in os.walk(data_folder_name+folder_name):

    # for file_id, filename in enumerate(files):

    # print(filename)
    key_without_extension, extension = os.path.splitext(key)
    # Find channels with these keywords
    check_names = ["event", "announce", "bullet",
                   "meet", "opportuni", "intern", "week", "social", "resourc", "competi", "gam", "info", "sched", "promo"]
    flag = False
    if extension == ".json":
        for name in check_names:
            if name in key.lower():
                flag = True

        if flag:
            print(key)
            folders = key.split('/')

            if len(folders) > 1:
                # Get Organization name
                org = folders[1]
                print(org)
            else:
                print("There's no org in the given key.")
                continue

            data = get_json_from_s3(key)

            if data == [] or data['messages'] == []:
                continue

            print(data['messages'][0]['id'])

            # set default image in case no image found
            default_image = data['guild']['iconUrl']

            creator_id = data['guild']['id']

            name_disc = data['guild']['name']

            for message in data['messages']:

                text = message['content']
                # print(text)

                # Parse the timestamp from the message
                message_timestamp = parser.isoparse(message['timestamp'])

                # Get current datetime
                current_datetime = datetime.now(message_timestamp.tzinfo)

                # Check if message timestamp was within the last 3 months
                difference = current_datetime - message_timestamp

                # assuming an average month is 30 days
                if difference > timedelta(days=3*30):
                    # print("The message was not within the last 3 months.")
                    continue

                try:
                    date_time_stacks = get_time(message)
                except Exception as e:
                    print(e)
                    print("date time EXCEPTION!!!!")
                    date_time_stacks = []
                    exception_count += 1
                    print(exception_count)
                    pass

                if date_time_stacks != []:
                    print(".")
                    loc_stack = get_loc(message['content'])
                    # loc_stack = ["to be decided"]
                    urls = re.findall(r'(https?://\S+)',
                                      message['content'])

                    if loc_stack != [] or urls != []:
                        # Extract image from text
                        image_url = default_image  # set image
                        if message['attachments'] != []:
                            # if there are attached images
                            for image in message['attachments']:
                                if 'png' in image['url'] or 'jpg' in image['url']:
                                    print(
                                        "\nImage Exists in message", image['url'])
                                    image_url = image['url']
                                    break

                        print("name_disc", name_disc)
                        print(message['content'])

                        event_dict = {}
                        print("creator_id: ", creator_id)
                        event_dict["CreatorID"] = creator_id
                        event_dict["Image"] = image_url
                        event_dict["Name"] = name_disc

                        date_time_val = str(date_time_stacks['date_stack'][0]+" "+date_time_stacks['time_stack'][0].replace(
                            'pm', '').replace('am', '')+" "+date_time_stacks['time_of_day'].upper())
                        if ":" not in date_time_val:
                            date_time_val = date_time_val[:-3] + \
                                ":00"+date_time_val[-3:]

                        try:
                            # Handle properly
                            date_time_val = datetime.strptime(
                                date_time_val, '%Y/%m/%d %I:%M %p')
                        except:
                            print("formatting error!!!!!!",
                                  date_time_val)
                            continue

                        date_time_val = date_time_val.isoformat()
                        date_time_val = parser.parse(date_time_val)
                        date_time_val = datetime.utcfromtimestamp(
                            date_time_val.timestamp())

                        event_dict["startingTime"] = str(date_time_val)

                        if loc_stack == []:
                            event_dict["Location"] = urls[0]
                        else:
                            event_dict["Location"] = loc_stack[0]

                        event_dict["Description"] = message['content'].replace(
                            '@', '')
                        event_dict["Visibility"] = "Public"

                        print(cnt)
                        cnt += 1

                        # image_string = process_image(event["Image"])

                        event_image = Image(event_dict["Image"])
                        event_image.process()

                        interest_ids = ["Social"]

                        # Convert the string to a datetime object
                        date_obj = datetime.strptime(
                            str(event_dict["startingTime"]), '%Y-%m-%d %H:%M:%S') + timedelta(minutes=1)
                        endtime = str(date_obj.strftime('%Y-%m-%d %H:%M:%S'))

                        append_to_json_file('all_events.json', event_dict)

                        print("Finallll event_dict:", event_dict)
