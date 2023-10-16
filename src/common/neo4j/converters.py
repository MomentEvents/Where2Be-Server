def convert_user_entity_to_user(data, show_num_events_followers_following=False, get_push_token=False):
    user_data = {
        "user_id": data["UserID"],
        "display_name": data["DisplayName"],
        "username": data["Username"],
        "picture": data["Picture"],
        "verified_organization": data.get("VerifiedOrganization", False),
    }

    if (get_push_token): 
        user_data['token']= data["PushTokens"]


    if(show_num_events_followers_following):
        user_data['num_followers'] = data["NumFollowers"]
        user_data['num_following'] = data["NumFollowing"]
        user_data['num_events'] = data["NumEvents"]
        user_data['user_follow'] = data["UserFollow"]

    return user_data


def convert_event_entity_to_event(data):
    event_data = {
        "event_id": data["EventID"],
        "picture": data["Picture"],
        "title": data["Title"],
        "description": data["Description"],
        "location": data["Location"],
        "start_date_time": str(data["StartDateTime"]),
        "end_date_time": None if data["EndDateTime"] == "NULL" else str(data["EndDateTime"]),
        "visibility": data["Visibility"]
    }

    # if num joins is asked, num shoutout is asked as well
    if("num_joins" in data):
        event_data["num_joins"] = data["num_joins"]

    if("num_shoutouts" in data):        
        event_data['num_shoutouts'] = data["num_shoutouts"]

    if("user_join" in data):
        event_data["user_join"] = data["user_join"]

    if("user_shoutout" in data):
        event_data["user_shoutout"] = data["user_shoutout"]

    if("user_follow_host" in data):
        event_data["user_follow_host"] = data["user_follow_host"]
    
    if("host_user_id" in data):
        event_data['host_user_id'] = data["host_user_id"]
    
    if("SignupLink" in data and data["SignupLink"] is not None):
        event_data["signup_link"] = data["SignupLink"]


    return event_data
    
def convert_school_entity_to_school(data):
    school_data = {
        "school_id": data["SchoolID"],
        "name": data["Name"],
        "abbreviation": data["Abbreviation"],
        "latitude": data["Latitude"],
        "longitude": data["Longitude"],
    }

    return school_data

def convert_moment_entity_to_moment(data):
    moment_data = {
        'moment_id': data['MomentID'],
        'moment_picture': data['MomentPicture'],
        'type': data['Type'],
        'posted_date_time': str(data['PostedDateTime']),
    }

    return moment_data