from cloud_resources.moment_neo4j import get_neo4j_session
from database_resources.commands import create_user_entity, create_event_entity, create_interest_entity, create_school_entity


do_fill_data = False
do_create_schema = True


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
        "CREATE INDEX IF NOT EXISTS ON :user_shoutout(DoNotify)",
    ]

    #Run initializing the schema here
    with get_neo4j_session() as session:
        for schema in schemas:
            try:
                session.run(schema)
            except Exception as e:
                print("Could not run schema " + schema + "\n\n" + str(e))
    return 1


def fill_data():
    school1_id = create_school_entity("test_univ", "Test University", "TU")
    interest1_id = create_interest_entity("academic", "Academic")
    interest2_id = create_interest_entity("athletic", "Athletic")
    interest3_id = create_interest_entity("social", "Social")
    interest4_id = create_interest_entity("professional", "Professional")
    user_access_token_1 = create_user_entity("Test User 1", "test1", "test1@ucsd.edu", "testuser1", False, school1_id)
    user_access_token_2 = create_user_entity("Test User 2", "test2", "test2@ucsd.edu", "testuser2", False, school1_id)
    create_event_entity(user_access_token_1, "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Frog_on_palm_frond.jpg/1024px-Frog_on_palm_frond.jpg",
    "Nature", "Look at my description :D", "La Jolla Shores", "Public", [interest1_id], "2024-04-20 17:00:00", "2024-04-20 18:00:00")
    create_event_entity(user_access_token_2, "https://iso.500px.com/wp-content/uploads/2015/03/business_cover.jpeg",
    "Nerdy Event", "Nerds only", "Geisel", "Public", [interest2_id], "2024-02-20 13:00:00", "2024-02-20 13:30:00")
    return 1

def init_db():
    if do_create_schema is True:
        init_schema()

    if do_fill_data is True:
        fill_data()

