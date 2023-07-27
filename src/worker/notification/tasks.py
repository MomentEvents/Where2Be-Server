from common.neo4j.commands.schoolcommands import get_all_school_entities
from common.neo4j.moment_neo4j import get_neo4j_session
from common.utils import send_and_validate_expo_push_notifications

import time
import asyncio


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

async def get_and_set_all_starting_soon_events(lookahead_period_min: int):

    with get_neo4j_session() as session:
        event_data = dict()

        result = session.run(
            """
            MATCH (s:School)<-[:event_school]-(e:Event)
            WITH e, size((e)<-[:user_joined]-()) + size((e)<-[:user_shoutout]-()) AS Popularity
            ORDER BY Popularity DESC
            RETURN e
            LIMIT 1""",
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
                asyncio.create_task(send_and_validate_expo_push_notifications(user_access_token, "New event posted", message, extra))
            except Exception as e:
                print(f"Error sending push notification for event_id {event_id}: \n\n{str(e)}")
        
    return 0

async def notify_recommended_events():
    school_entities = get_all_school_entities()

    for school_entity in school_entities:

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
            asyncio.create_task(send_and_validate_expo_push_notifications(user_access_token, "New event posted", message, extra))
        except Exception as e:
            print(f"Error sending push notification for event_id {event_id}: \n\n{str(e)}")
        
    return 0

    #   you have free control to do this
    
        test = 1
    return 0

# start_time = time.time()
# notify_all_events_starting_soon()
# print("--- %s seconds ---" % (time.time() - start_time))

