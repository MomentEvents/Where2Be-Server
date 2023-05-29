
def convert_user_entity_to_user(data):
    user_data = {
        "user_id": data["UserID"],
        "display_name": data["DisplayName"],
        "username": data["Username"],
        "picture": data["Picture"],
        "verified_organization": data.get("VerifiedOrganization", False),
    }

    return user_data

    
def convert_school_entity_to_school(data):
    school_data = {
        "school_id": data["SchoolID"],
        "name": data["Name"],
        "abbreviation": data["Abbreviation"],
        "latitude": data["Latitude"],
        "longitude": data["Longitude"],
    }

    return school_data