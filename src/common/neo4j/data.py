from common.neo4j.moment_neo4j import get_neo4j_session
from common.neo4j.commands.usercommands import create_follow_connection, create_user_entity
from common.neo4j.commands.schoolcommands import create_school_entity
from common.neo4j.commands.interestcommands import create_interest_entity
from common.neo4j.commands.eventcommands import create_event_entity

import os
from common.constants import IS_PROD

do_reset_db = False
do_create_schema = False

def init_schema():
    schemas = [
        # Users
        "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.UserID IS UNIQUE", # String
        "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.Email IS UNIQUE;", # String
        "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.Username IS UNIQUE", # String
        "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.UserAccessToken IS UNIQUE;", # String
        "CREATE INDEX IF NOT EXISTS FOR (u:User) ON (u.DisplayName);", # String
        "CREATE INDEX IF NOT EXISTS FOR (u:User) ON (u.PasswordHash);", # Object
        "CREATE INDEX IF NOT EXISTS FOR (u:User) ON (u.Picture);", # String
        "CREATE INDEX IF NOT EXISTS FOR (u:User) ON (u.VerifiedOrganization);", # Boolean
        "CREATE INDEX IF NOT EXISTS FOR (u:User) ON (u.Administrator);", # Boolean
        #Events
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Event) REQUIRE e.EventID IS UNIQUE", # String
        "CREATE INDEX IF NOT EXISTS FOR (e:Event) ON (e.Title);", # String
        "CREATE INDEX IF NOT EXISTS FOR (e:Event) ON (e.Description);", # String
        "CREATE INDEX IF NOT EXISTS FOR (e:Event) ON (e.Picture);", # String
        "CREATE INDEX IF NOT EXISTS FOR (e:Event) ON (e.Location);", # String
        "CREATE INDEX IF NOT EXISTS FOR (e:Event) ON (e.StartDateTime);", # String / null
        "CREATE INDEX IF NOT EXISTS FOR (e:Event) ON (e.EndDateTime);", # String
        "CREATE INDEX IF NOT EXISTS FOR (e:Event) ON (e.TimeCreated);", # Date
        #Schools
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:School) REQUIRE s.SchoolID IS UNIQUE", # String
        "CREATE INDEX IF NOT EXISTS FOR (s:School) ON (s.Name);", # String
        "CREATE INDEX IF NOT EXISTS FOR (s:School) ON (s.Abbreviation);", # String
        "CREATE INDEX IF NOT EXISTS FOR (s:School) ON (s.Latitude);", # Float
        "CREATE INDEX IF NOT EXISTS FOR (s:School) ON (s.Longitude);", # Float
        #Interests
        "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Interest) REQUIRE i.InterestID IS UNIQUE", # String
        "CREATE INDEX IF NOT EXISTS FOR (i:Interest) ON (i.Name);", # String

        #user_shoutout
        "CREATE INDEX IF NOT EXISTS FOR ()-[r:user_shoutout]->() ON (r.DoNotify);", #Bool
        "CREATE INDEX IF NOT EXISTS FOR ()-[r:user_shoutout]->() ON (r.MinutesToNotify);", #Int
        "CREATE INDEX IF NOT EXISTS FOR ()-[r:user_shoutout]->() ON (r.DidNotify);", #Bool

        #user_join
        "CREATE INDEX IF NOT EXISTS FOR ()-[r:user_join]->() ON (r.DoNotify);", #Bool
        "CREATE INDEX IF NOT EXISTS FOR ()-[r:user_join]->() ON (r.MinutesToNotify);", #Int
        "CREATE INDEX IF NOT EXISTS FOR ()-[r:user_join]->() ON (r.DidNotify);", #Bool

        #user_host
        "CREATE INDEX IF NOT EXISTS FOR ()-[r:user_host]->() ON (r.DoNotify);", #Bool
        "CREATE INDEX IF NOT EXISTS FOR ()-[r:user_host]->() ON (r.MinutesToNotify);", #Int
        "CREATE INDEX IF NOT EXISTS FOR ()-[r:user_host]->() ON (r.DidNotify);", #Bool

        #user_follow
        "CREATE INDEX IF NOT EXISTS FOR ()-[r:user_follow]->() ON (r.Timestamp);", #DateTime
        "CREATE INDEX IF NOT EXISTS FOR ()-[r:user_follow]->() ON (r.EventNotify);", #Bool

        #user_school
        "CREATE INDEX IF NOT EXISTS FOR ()-[r:user_school]->() ON (r.NullAttribute)", #null

        #event_tag
        "CREATE INDEX IF NOT EXISTS FOR ()-[r:event_tag]->() ON (r.NullAttribute)", #null

        #event_school
        "CREATE INDEX IF NOT EXISTS FOR ()-[r:event_school]->() ON (r.NullAttribute)", #null
    ]

    #Run initializing the schema here
    with get_neo4j_session() as session:
        for schema in schemas:
            try:
                session.run(schema)
            except Exception as e:
                print("\n\n" + str(e))
    return 1


def fill_data():    
    school1_id = create_school_entity("test_univ", "Test University", "TU", 32.8801, 117.2340)
    school2_id = create_school_entity("test_univ", "Test University 2", "TU2", 30.4233, 100.4323)
    interest1_id = create_interest_entity("academic", "Academic")
    interest2_id = create_interest_entity("athletic", "Athletic")
    interest3_id = create_interest_entity("social", "Social")
    interest4_id = create_interest_entity("professional", "Professional")
    user_access_token_1, user_id_1 = create_user_entity("MomentOrg", "momentorg", school1_id, True, False)
    user_access_token_2, user_id_2 = create_user_entity("Test User 1", "testuser1", school1_id, False, False)
    user_access_token_3, user_id_3 = create_user_entity("MomentAdmin", "momentadmin", school1_id, True, True)
    user_access_token_4, user_id_4 = create_user_entity("Test User 2", "testuser2", school1_id, False, False)
    user_access_token_5, user_id_5 = create_user_entity("Test User @ TU2", "testuser2", school2_id, False, False)
    user_access_token_6, user_id_6 = create_user_entity("Test User 3", "testuser3", school1_id, False, False)
    user_access_token_7, user_id_7 = create_user_entity("Test User 4", "testuser4", school1_id, False, False)
    user_access_token_8, user_id_8 = create_user_entity("Test User 5", "testuser5", school1_id, False, False)
    user_access_token_9, user_id_9 = create_user_entity("Test User 6", "testuser6", school1_id, False, False)
    user_access_token_10, user_id_10 = create_user_entity("Test User 7", "testuser7", school1_id, False, False)
    user_access_token_11, user_id_11 = create_user_entity("Test User 8", "testuser8", school1_id, False, False)
    user_access_token_12, user_id_12 = create_user_entity("Test User 9", "testuser9", school1_id, False, False)
    user_access_token_13, user_id_13 = create_user_entity("Test User 10", "testuser10", school1_id, False, False)
    user_access_token_14, user_id_14 = create_user_entity("Test User 11", "testuser11", school1_id, False, False)
    user_access_token_15, user_id_15 = create_user_entity("Test User 12", "testuser12", school1_id, False, False)
    user_access_token_16, user_id_16 = create_user_entity("Test User 13", "testuser13", school1_id, False, False)
    user_access_token_17, user_id_17 = create_user_entity("Test User 14", "testuser14", school1_id, False, False)
    user_access_token_18, user_id_18 = create_user_entity("Test User 15", "testuser15", school1_id, False, False)
    user_access_token_19, user_id_19 = create_user_entity("Test User 16", "testuser16", school1_id, False, False)
    user_access_token_20, user_id_20 = create_user_entity("Test User 17", "testuser17", school1_id, False, False)
    user_access_token_21, user_id_21 = create_user_entity("Test User 18", "testuser18", school1_id, False, False)
    user_access_token_22, user_id_22 = create_user_entity("Test User 19", "testuser19", school1_id, False, False)
    user_access_token_23, user_id_23 = create_user_entity("Test User 20", "testuser20", school1_id, False, False)
    user_access_token_24, user_id_24 = create_user_entity("Test User 21", "testuser21", school1_id, False, False)
    user_access_token_25, user_id_25 = create_user_entity("Test User 22", "testuser22", school1_id, False, False)
    user_access_token_26, user_id_26 = create_user_entity("Test User 23", "testuser23", school1_id, False, False)
    user_access_token_27, user_id_27 = create_user_entity("Test User 24", "testuser24", school1_id, False, False)
    user_access_token_28, user_id_28 = create_user_entity("Test User 25", "testuser25", school1_id, False, False)
    user_access_token_29, user_id_29 = create_user_entity("Test User 26", "testuser26", school1_id, False, False)
    user_access_token_30, user_id_30 = create_user_entity("Test User 27", "testuser27", school1_id, False, False)

    create_follow_connection(user_id_6, user_id_1)
    create_follow_connection(user_id_7, user_id_1)
    create_follow_connection(user_id_8, user_id_1)
    create_follow_connection(user_id_9, user_id_1)
    create_follow_connection(user_id_10, user_id_1)
    create_follow_connection(user_id_11, user_id_1)
    create_follow_connection(user_id_12, user_id_1)
    create_follow_connection(user_id_13, user_id_1)
    create_follow_connection(user_id_14, user_id_1)
    create_follow_connection(user_id_15, user_id_1)
    create_follow_connection(user_id_16, user_id_1)
    create_follow_connection(user_id_17, user_id_1)
    create_follow_connection(user_id_18, user_id_1)
    create_follow_connection(user_id_19, user_id_1)
    create_follow_connection(user_id_20, user_id_1)
    create_follow_connection(user_id_21, user_id_1)
    create_follow_connection(user_id_22, user_id_1)
    create_follow_connection(user_id_23, user_id_1)
    create_follow_connection(user_id_24, user_id_1)
    create_follow_connection(user_id_25, user_id_1)
    create_follow_connection(user_id_26, user_id_1)
    create_follow_connection(user_id_27, user_id_1)
    create_follow_connection(user_id_28, user_id_1)
    create_follow_connection(user_id_29, user_id_1)
    create_follow_connection(user_id_30, user_id_1)

    event_start_dates = "2023-07-16"
    event_end_dates = "2023-07-16"

    create_event_entity(user_access_token_1, "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Frog_on_palm_frond.jpg/1024px-Frog_on_palm_frond.jpg",
    "Nature", "Look at my description :D", "La Jolla Shores", "Public", [interest1_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_2, "https://www.theforage.com/blog/wp-content/uploads/2022/10/stock-options.jpg",
    "Tech Event", "Look at my description :D", "La Jolla Shores", "Public", [interest1_id], event_start_dates + " 11:00:00", event_end_dates + " 13:00:00")
    create_event_entity(user_access_token_3, "https://expertphotography.b-cdn.net/wp-content/uploads/2020/06/stock-photography-trends11.jpg",
    "Music Jam", "Look at my description :D", "La Jolla Shores", "Public", [interest3_id], event_start_dates + " 09:00:00", event_end_dates + " 12:00:00")
    create_event_entity(user_access_token_4, "https://umbrellacreative.com.au/wp-content/uploads/2020/01/hide-the-pain-harold-why-you-should-not-use-stock-photos-1024x683.jpg",
    "Nature", "Look at my description :D", "La Jolla Shores", "Public", [interest4_id], event_start_dates + " 14:30:00", event_end_dates + " 15:30:00")
    create_event_entity(user_access_token_2, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
    "Nerdy Event", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")

    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 1", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 2", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 3", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 4", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 5", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 6", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 7", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 8", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 9", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 10", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 11", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 12", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event1 13", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 14", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 15", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 16", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 17", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 18", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 19", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 20", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 21", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 22", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 23", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 24", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    create_event_entity(user_access_token_8, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
"Nerdy Event 25", "Nerds only", "Geisel", "Public", [interest2_id], event_start_dates + " 17:00:00", event_end_dates + " 18:00:00")
    return 1

def reset_db():
    if IS_PROD is True:
        return
    
    with get_neo4j_session() as session:
        session.run("""MATCH (n)
            DETACH DELETE n""")
    return 1

def init_neo4j():
    if do_reset_db is True and IS_PROD is False:
        reset_db()
        fill_data()
    if do_create_schema is True:
        init_schema()
