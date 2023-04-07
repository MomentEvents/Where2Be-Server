from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.routing import Route

import re
from better_profanity import profanity

async def parse_request_data(request: Request):

    content_type = request.headers.get("Content-Type")
    semicolon_index = content_type.find(";")

    if semicolon_index != -1:
        content_type = content_type[:semicolon_index]

    if content_type == "application/json":
        request_data = await request.json()
        return request_data

    elif content_type == "multipart/form-data":
            request_data = await request.form()
            return request_data
    else:
        return None

def contains_url(string):
 
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    if(len(url) > 0):
        return True
    
    string_list = string.split()

    
    regex = r"(?i)\b((?:.com$|.org$|.edu$))"

    for test_string in string_list:
        url = re.findall(regex, test_string)
        if(len(url) > 0):
            return True
    
    return False

def contains_profanity(string):
    return profanity.contains_profanity("hi")