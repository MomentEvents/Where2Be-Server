def convert_user_entity_to_user(data, show_num_events_followers_following: bool):
    user_data = {
        "user_id": data["UserID"],
        "display_name": data["DisplayName"],
        "username": data["Username"],
        "picture": data["Picture"],
        "verified_organization": data.get("VerifiedOrganization", False),
    }

    if(show_num_events_followers_following):
        user_data['num_followers'] = data["NumFollowers"]
        user_data['num_following'] = data["NumFollowing"]
        user_data['num_events'] = data["NumEvents"]
        user_data['user_follow'] = data["UserFollow"]

    return user_data


# def convert_event_entity_to_event(data):
#     event_data = {
#         "event_id": data['event_id'],
#         "title": data['title'],
#         "picture": data['picture'],
#         description = data['description'],
#         location = data['location'],
#         start_date_time = str(data['start_date_time']),
#         end_date_time = None if data["end_date_time"] == "NULL" else str(data["end_date_time"])
#         visibility = data['visibility']
#         num_joins = data['num_joins']
#         num_shoutouts = data['num_shoutouts']
#         user_join = data['user_join']
#         user_shoutout = data['user_shoutout']
#         host_user_id = data['host_user_id']
#     }

#     return school_data

    
def convert_school_entity_to_school(data):
    school_data = {
        "school_id": data["SchoolID"],
        "name": data["Name"],
        "abbreviation": data["Abbreviation"],
        "latitude": data["Latitude"],
        "longitude": data["Longitude"],
    }

    return school_data