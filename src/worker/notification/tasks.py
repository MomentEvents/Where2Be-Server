from common.neo4j.commands.schoolcommands import get_all_school_entities, get_all_users_by_school
from common.neo4j.commands.eventcommands import get_random_popular_event_within_x_days

from common.neo4j.moment_neo4j import get_neo4j_session
from common.utils import send_and_validate_expo_push_notifications, store_runtime

import concurrent.futures

import time
import asyncio
import random

def random_message():
    messages = [
    "Get ready to join the crowd!",
    "Stay in the loop!",
    "Be a part of something big!",
    "Don't miss out!",
    "Join the fun!",
    "Are you ready for this?",
    "Something big is happening!",
    "This is what you've been waiting for!",
    "Get in on the action!",
    "The buzz is all about this!",
    "Catch the excitement!",
    "The crowd is gathering!",
    "Can you feel the anticipation?",
    "This is going to be epic!",
    "It's time to make some memories!",
    "You won't want to miss this!",
    "Time to get your game face on!",
    "Ready for the highlight of your year?",
    "Be where everyone else will be!",
    "Jump into the fun!",
    "Be part of the next big thing!",
    "Are you ready to have a blast?",
    "You won't believe what's coming up!",
    "This is going to be unforgettable!",
    "Ready to make some noise?",
    "Get excited, it's nearly here!",
    ]
    return random.choice(messages)

async def get_and_set_all_starting_soon_events(lookahead_period_min: int):

    with get_neo4j_session() as session:
        event_data = dict()

        result = session.run(
            """
            MATCH (e:Event)-[rel:user_joined|user_host]-(u:User)
            WHERE datetime(e.StartDateTime) >= datetime() AND datetime(e.StartDateTime) <= datetime() + duration({months: $lookahead_period_min}) 
            AND (type(rel) = 'user_joined' OR type(rel) = 'user_host')
            RETURN e.Title AS title, e.EventID AS event_id, collect({user_id: u.UserID, user_access_token: u.UserAccessToken}) AS user_details""",
            parameters={
                "lookahead_period_min": lookahead_period_min,
            }
        )
        for record in result:
            event_id = record['event_id']
            if event_id not in event_data:
                event_data[event_id] = [record['title'], record['user_details']]
        
        return event_data

async def notify_all_events_starting_soon():

    event_data = await get_and_set_all_starting_soon_events(lookahead_period_min=3)

    # Iterate over each event in event_data
    for event_id, (event_title, users) in event_data.items():

        for user in users:
            user_id = user['user_id']
            user_access_token = user['user_access_token']

            message = f"\"{event_title}\" is starting soon!"
            
            # Prepare the extra information to be sent with the notification
            extra = {
                'action': 'ViewEventDetails',
                'event_id': event_id,
            }

            # Send and validate notifications
            try:
                asyncio.create_task(send_and_validate_expo_push_notifications(user_access_token, "Event starting soon", message, extra))
            except Exception as e:
                print(f"Error sending push notification for event_id {event_id} for user {user_access_token}: \n\n{str(e)}")

    store_runtime("notify_all_events_starting_soon")

    return 0

async def notify_recommended_events():
    school_entities = get_all_school_entities()

    tasks = []

    for school in school_entities:
        print(school)

        # Create the tasks and add them to our list
        # check with multiple univs
        asyncio.create_task(
            get_and_notify_for_school(school)
        )

    store_runtime("notify_recommended_events")

async def get_and_notify_for_school(school):
    # Get the event
    event = await get_random_popular_event_within_x_days(days=60, school_id=school['school_id'])

    if event == None:
        print(f"School {school['name']} has no events coming up")
        return

    print(f"Event from school {school['name']} is event: {event['title']}")

    # Get the users connected to the school
    users = get_all_users_by_school(school['school_id'])

    # Prepare the notification
    random_initial_message = random_message() 
    message = f"{random_initial_message} {event['title']} is getting popular at your school."
    extra = {
        'action': 'ViewEventDetails',
        'event_id': event['event_id'],
    }

    for user in users:
        user_access_token = user['user_access_token']
        try:
            # Create task for sending notification
            asyncio.create_task(send_and_validate_expo_push_notifications(user_access_token, "Popular event notification", message, extra))
        except Exception as e:
            print(f"Error sending push notification for user_id {user['user_id']}: \n\n{str(e)}")
        
# start_time = time.time()
# notify_all_events_starting_soon()
# print("--- %s seconds ---" % (time.time() - start_time))

