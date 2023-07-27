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


def convert_event_entity_to_event(data, user_exists = True):
    event_data = {
        "event_id": data["event_id"],
        "picture": data["picture"],
        "title": data["title"],
        "description": data["description"],
        "location": data["location"],
        "start_date_time": str(data["start_date_time"]),
        "end_date_time": None if data["end_date_time"] == "NULL" else str(data["end_date_time"]),
        "visibility": data["visibility"],
        "num_joins": data["num_joins"],
        "num_shoutouts": data["num_shoutouts"],
        "host_user_id": data["host_user_id"],
    }

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