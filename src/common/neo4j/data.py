from common.neo4j.moment_neo4j import get_neo4j_session
from common.commands import create_user_entity, create_event_entity, create_interest_entity, create_school_entity, signup
import os

do_reset_db = False
do_create_schema = False

is_prod = os.environ.get('IS_PROD') # This is a sanity check so we don't accidently reset the DB if it is prod :)

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
    interest1_id = create_interest_entity("academic", "Academic")
    interest2_id = create_interest_entity("athletic", "Athletic")
    interest3_id = create_interest_entity("social", "Social")
    interest4_id = create_interest_entity("professional", "Professional")
    user_access_token_1 = signup("TestUser1", "Test User 1", "clarificationdorad@gmail.com", "test1234", school1_id)
    user_access_token_2 = signup("TestUser2", "Test User 2", "clarificationdorad2@gmail.com", "test1234", school1_id)
    user_access_token_3 = signup("TestUser3", "Test User 3", "clarificationdorad3@gmail.com", "test1234", school1_id)
    user_access_token_4 = signup("TestUser4", "Test User 4", "clarificationdorad4@gmail.com", "test1234", school1_id)

    create_event_entity(user_access_token_1, "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Frog_on_palm_frond.jpg/1024px-Frog_on_palm_frond.jpg",
    "Nature", "Look at my description :D", "La Jolla Shores", "Public", [interest1_id], "2023-06-02 17:00:00", "2023-06-02 18:00:00")
    create_event_entity(user_access_token_2, "https://www.theforage.com/blog/wp-content/uploads/2022/10/stock-options.jpg",
    "Tech Event", "Look at my description :D", "La Jolla Shores", "Public", [interest1_id], "2023-06-02 17:00:00", "2023-06-02 18:00:00")
    create_event_entity(user_access_token_3, "https://expertphotography.b-cdn.net/wp-content/uploads/2020/06/stock-photography-trends11.jpg",
    "Music Jam", "Look at my description :D", "La Jolla Shores", "Public", [interest3_id], "2023-06-02 17:00:00", "2023-06-02 18:00:00")
    create_event_entity(user_access_token_4, "https://umbrellacreative.com.au/wp-content/uploads/2020/01/hide-the-pain-harold-why-you-should-not-use-stock-photos-1024x683.jpg",
    "Nature", "Look at my description :D", "La Jolla Shores", "Public", [interest4_id], "2023-06-02 17:00:00", "2023-06-02 18:00:00")
    create_event_entity(user_access_token_2, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
    "Nerdy Event", "Nerds only", "Geisel", "Public", [interest2_id], "2023-06-02 13:00:00", "2023-06-02 13:30:00")
    return 1

def reset_db():
    with get_neo4j_session() as session:
        session.run("""MATCH (n)
            DETACH DELETE n""")
    return 1

def init_neo4j():
    if do_reset_db is True:
        reset_db()
        fill_data()
    if do_create_schema is True:
        init_schema()
    test = 1
