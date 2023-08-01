def convert_user_entity_to_user(data, show_num_events_followers_following=False, get_push_token=False):
    user_data = {
        "user_id": data["UserID"],
        "display_name": data["DisplayName"],
        "username": data["Username"],
        "picture": data["Picture"],
        "verified_organization": data.get("VerifiedOrganization", False),
    }

    if (get_push_token): 
        user_data['user_access_token']= data["UserAccessToken"]


    if(show_num_events_followers_following):
        user_data['num_followers'] = data["NumFollowers"]
        user_data['num_following'] = data["NumFollowing"]
        user_data['num_events'] = data["NumEvents"]
        user_data['user_follow'] = data["UserFollow"]

    return user_data


def convert_event_entity_to_event(data, user_exists = False, get_host_and_connections=False):
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

    if get_host_and_connections:
        event_data['num_joins'] = data["num_joins"]
        event_data['num_shoutouts'] = data["num_shoutouts"]
        event_data['host_user_id'] = data["host_user_id"]
        event_data['user_shoutout'] = data["user_shoutout"]

    if(user_exists):
        event_data['user_join'] = data["user_join"]
        event_data['user_shoutout'] = data["user_shoutout"]

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