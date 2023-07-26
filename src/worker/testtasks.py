from common.neo4j.commands.schoolcommands import get_all_school_entities


async def notify_all_events_starting_soon():
    # [event_ids, event_title] with each user_ids[], user_push_tokens[] = await get_and_set_all_starting_soon_events()
    # get_and_set_all_starting_soon_events()
    # 1. Gets all events that are starting withing an hour in the future. Then it gets all user_joins and user_host when did_notify is false
    # 2. Through all those users that are connected with those relationships, we get their expo push tokens and user_ids similar to what is done
    # on notificationcommands.py. We then map it to a pair of event_ids and event_title
    # 3. Loop through each unique event_id pair and call

    # for unique event_id
    #   [all parallel] send_and_validate_expo_push_notifications(tokens_with_user_id: "set[dict[str, str]]", title: str, message: str, extra)

    # Here is an example on how to call that function through eventservice.

    # if(ping_followers):
    # print("PINGING FOLLOWERS")
    # try:
    #     follower_push_tokens_with_user_id = get_all_follower_push_tokens(user['user_id'])
    #     if(follower_push_tokens_with_user_id is not None):
    #         send_and_validate_expo_push_notifications(follower_push_tokens_with_user_id, "New event posted", "" + str(user["username"] + " just posted \"" + str(title)) + "\"", {
    #             'action': 'ViewEventDetails',
    #             'event_id': event_id,
    #         })
    # except Exception as e:
    #     print("ERROR SENDING FOLLOWER PUSH NOTIFICATION: \n\n" + str(e))


    return 0

async def notify_recommended_events():
    school_entities = get_all_school_entities()

    for school_entity in school_entities:
    #   [all parallel] notify_recommended_school_event(school_entity['school_id'])

    #   you have free control to do this
    
        test = 1
    return 0