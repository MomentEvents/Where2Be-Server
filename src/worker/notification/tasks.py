from common.neo4j.commands.schoolcommands import get_all_school_entities, get_all_users_by_school
from common.neo4j.commands.eventcommands import get_random_popular_event_within_x_days, get_events_created_after_given_time, get_and_notify_all_starting_soon_events, user_isnotified
from common.neo4j.commands.usercommands import get_all_bots, create_join_connection, create_shoutout_connection


from common.utils import send_and_validate_expo_push_notifications, store_runtime

import concurrent.futures

import time
import asyncio
import random


async def notify_all_events_starting_soon():

    event_data = await get_and_notify_all_starting_soon_events(lookahead_period_min=60)

    # Iterate over each event in event_data
    for event_id, (event_title, user_ids_with_push_tokens) in event_data.items():

        for user_id_with_push_token in user_ids_with_push_tokens:
            random_initial_message = random_message()

            message = f"{random_initial_message} \"{event_title}\" is starting soon!"
            formatted_user_id_with_push_token = [user_id_with_push_token]

            # Prepare the extra information to be sent with the notification
            extra = {
                'action': 'ViewEventDetails',
                'event_id': event_id,
            }

            # Send and validate notifications
            try:
                asyncio.create_task(send_and_validate_expo_push_notifications(
                    formatted_user_id_with_push_token, "Event starting soon", message, extra, isnotified=True))

            except Exception as e:
                print(
                    f"Error sending push notification for event_id {event_id} for user {formatted_user_id_with_push_token}: \n\n{str(e)}")

    store_runtime("notify_all_events_starting_soon")

    return 0


async def notify_recommended_events():
    school_entities = await get_all_school_entities()

    for school in school_entities:
        asyncio.create_task(get_and_notify_for_school(school))

    # Await all tasks to complete
    # await asyncio.gather(*tasks)

    store_runtime("notify_recommended_events")


async def get_and_notify_for_school(school):
    # Get the event
    event = await get_random_popular_event_within_x_days(days=60, school_id=school['school_id'])

    if event == None:
        print(f"School {school['name']} has no events coming up")
        return

    print(f"Event from school {school['name']} is event: {event['title']}")

    # Get the users connected to the school
    users = await get_all_users_by_school(school['school_id'])

    # Prepare the notification
    random_initial_message = random_message()
    message = f"{random_initial_message} \"{event['title']}\" is getting popular at your school."
    extra = {
        'action': 'ViewEventDetails',
        'event_id': event['event_id'],
    }

    # print(users)
    for user_id_with_push_token in users:
        print(user_id_with_push_token)
        try:
            # Create task for sending notification
            asyncio.create_task(send_and_validate_expo_push_notifications(
                user_id_with_push_token, "Popular event notification", message, extra))
        except Exception as e:
            print(
                f"Error sending push notification for user_id {user_id_with_push_token['user_id']}: \n\n{str(e)}")


async def bot_chance_join_repost_event(event_id):

    # Get all bots
    bots = await get_all_bots()

    for bot in bots:
        user_id = bot['user_id']
        chance = random.randint(0, 60) / 100

        if random.random() < chance:
            print("join for ", event_id)
            await create_join_connection(user_id, event_id)

        if random.random() < (chance + 0.25):
            print("shoutout for ", event_id)
            await create_shoutout_connection(user_id, event_id)

        await asyncio.sleep(random.randint(0, 120))


async def perform_bot_actions(last_run_time):

    print("last_run_time", last_run_time)

    # Get all events created after the last run
    new_events = await get_events_created_after_given_time(last_run_time)

    if not new_events:
        return

    tasks = []
    store_runtime("perform_bot_actions")

    # Loop through each bot and each event
    for event in new_events:
        asyncio.create_task(bot_chance_join_repost_event(event['event_id']))
        # tasks.append(task)

    # Now we use gather to run all tasks concurrently
    # await asyncio.gather(*tasks)


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
        "Catch the excitement!",
        "The crowd is gathering!",
        "Can you feel the anticipation?",
        "It's time to make some memories!",
        "You won't want to miss this!",
        "Time to get your game face on!",
        "Be where everyone else will be!",
        "Jump into the fun!",
        "Are you ready to have a blast?",
        "Ready to make some noise?",
        "Get excited, it's nearly here!",
        "The countdown is on!",
        "Ready to be amazed?",
        "You're invited to something special!",
        "A day you won't forget!",
        "Brace yourself for the unexpected!",
        "The time is now!",
        "The best is yet to come!",
        "Time to turn the excitement up a notch!",
        "The wait is almost over!",
        "Gear up for an incredible experience!",
        "This is your moment!",
        "Embrace the excitement!",
        "Don't keep the fun waiting!",
        "You're in for a treat!"
    ]
    return random.choice(messages)
