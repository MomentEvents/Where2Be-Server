from py2neo import Graph, Node, Relationship
from cloud_resources.moment_neo4j import get_neo4j_session

from utils.helpers import get_hash_pwd, convert_datetime

class Neo4jDatabase:
    def __init__(self):
        self.user = Node("User", UserID="TestUser1", DisplayName="TestUser1", Username="testuser1",
                         PasswordHash=get_hash_pwd("testuser1"), Picture="", UserAccessToken="testuser1")

        self.event = Node("Event", EventID="testevent1", Title="testevent1", Description="testevent1", Picture="", Location="testevent1",
                          StartDateTime=convert_datetime("2024-04-10 12:30:00"), EndDateTime=convert_datetime("2024-04-10 13:30:00"), Visibility="Public", TimeCreated=convert_datetime("2024-04-10 12:30:00"))

        self.school = Node("School", SchoolID="testschool1", Name="TestSchool1",
                           Latitude="0", Longitude="0", Abbreviation="Test")

        self.interest = Node("Interest", InterestID="TestInterest1", Name="TestInterest1")

        self.session = get_neo4j_session()

    # initialize the database
    def init(self):
        self.create_user()
        self.create_event()
        self.create_school()
        self.create_index()
        # self.create_constraints()

    def create_index(self):
        with self.session.begin_transaction() as tx:

            # Index for user
            tx.run("CREATE INDEX IF NOT EXISTS FOR (u:User) ON (u.UserID)")
            # Index for event
            tx.run("CREATE INDEX IF NOT EXISTS FOR (e:Event) ON (e.EventID)")
            # Index for school
            tx.run("CREATE INDEX IF NOT EXISTS FOR (s:School) ON (s.SchoolID)")
            # Index for school
            tx.run("CREATE INDEX IF NOT EXISTS FOR (i:Interest) ON (i.InterestID)")

            tx.commit()

    def create_constraints(self):
        with self.session.begin_transaction() as tx:

            # constraints for user
            tx.run(
                "CREATE CONSTRAINT User_Unique IF NOT EXISTS FOR (u:User) REQUIRE (u.Username, u.UserAccessToken) IS UNIQUE")
            tx.run(
                "CREATE CONSTRAINT User_NotNull IF NOT EXISTS FOR (u:User) REQUIRE (u.UserID, u.Username, u.UserAccessToken) IS NOT NULL")
            # constraints for event
            tx.run(
                "CREATE CONSTRAINT Event_NotNull IF NOT EXISTS FOR (e:Event) REQUIRE (e.EventID, e.StartDateTime) IS NOT NULL")
            # constraints for school
            tx.run(
                "CREATE CONSTRAINT School_NotNull IF NOT EXISTS FOR (s:School) REQUIRE (s.SchoolID) IS NOT NULL")
            # constraints for school
            tx.run(
                "CREATE CONSTRAINT Interest_Unique IF NOT EXISTS FOR (i:Interest) REQUIRE (i.InterestID) IS UNIQUE")
            tx.run(
                "CREATE CONSTRAINT Interest_NotNull IF NOT EXISTS FOR (i:Interest) REQUIRE (i.InterestID) IS NOT NULL")

            tx.commit()

    def create_user(self):
        with self.session.begin_transaction() as tx:
            # Check if user node already exists
            result = tx.run(
                "MATCH (n:User {UserID: $UserID}) RETURN n", UserID=self.user["UserID"])
            existing_user = result.single()

            if existing_user is None:
                print("CREATING USER")
                # Create user node
                tx.run("CREATE (:User {UserID: $UserID, DisplayName: $DisplayName, Username: $Username, PasswordHash: $PasswordHash, Picture: $Picture, UserAccessToken: $UserAccessToken})",
                       **self.user)

            tx.commit()

    def create_event(self):
        with self.session.begin_transaction() as tx:
            # Check if event node already exists
            result = tx.run(
                "MATCH (n:Event {EventID: $EventID}) RETURN n", EventID=self.event["EventID"])
            existing_event = result.single()

            if existing_event is None:
                print("CREATING EVENT")
                # Create event node
                tx.run("CREATE (:Event {EventID: $EventID, Title: $Title, Description: $Description, Picture: $Picture, Location: $Location, StartDateTime: $StartDateTime, EndDateTime: $EndDateTime, Visibility: $Visibility, TimeCreated: $TimeCreated})",
                       **self.event)

            tx.commit()

    def create_school(self):
        with self.session.begin_transaction() as tx:
            # Check if school node already exists
            result = tx.run(
                "MATCH (n:School {SchoolID: $SchoolID}) RETURN n", SchoolID=self.school["SchoolID"])
            existing_school = result.single()

            if existing_school is None:
                print("CREATING SCHOOL")
                # Create school node
                tx.run("CREATE (:School {SchoolID: $SchoolID, Name: $Name, Latitude: $Latitude, Longitude: $Longitude, Abbreviation: $Abbreviation})",
                       **self.school)

            tx.commit()

    def create_interest(self):
        with self.session.begin_transaction() as tx:
            # Check if interest node already exists
            result = tx.run(
                "MATCH (n:Interest {InterestID: $InterestID}) RETURN n", InterestID=self.interest["InterestID"])
            existing_interest = result.single()

            if existing_interest is None:
                print("CREATING INTEREST")
                # Create interest node
                tx.run("CREATE (:Interest {InterestID: $InterestID, Name: $Name})",
                       **self.interest)

            tx.commit()
