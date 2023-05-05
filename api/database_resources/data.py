from cloud_resources.moment_neo4j import get_neo4j_session
import time


fill_data = False


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
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:School) REQUIRE e.SchoolID IS UNIQUE", # String
        "CREATE INDEX IF NOT EXISTS FOR (s:School) ON (s.Name);", # String
        "CREATE INDEX IF NOT EXISTS FOR (s:School) ON (s.Abbreviation);", # String
        #Interests
        "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Interest) REQUIRE i.InterestID IS UNIQUE", # String
        "CREATE INDEX IF NOT EXISTS FOR (i:Interest) ON (i.Name);", # String
    ]
    #Run initializing the schema here
    with get_neo4j_session() as session:
        for schema in schemas:
            try:
                session.run(schema)
            except:
                print("Could not run schema " + schema)
    return 1


def fill_data():
    #Run filling example data here
    return 1

def init_db():
    init_schema()

    if fill_data is True:
        fill_data()

