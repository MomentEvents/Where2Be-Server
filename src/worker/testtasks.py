from common.neo4j.commands.schoolcommands import get_all_school_entities


async def notify_all_events_starting_soon():
    # [event_ids, event_title] with each user_ids[], user_push_tokens[] = await get_and_set_all_starting_soon_events()

    # for unique event_id
    #   [all parallel] notify_push_tokens(event_tite, user_push_tokens)
    return 0

async def notify_recommended_events():
    school_entities = get_all_school_entities()

    for school_entity in school_entities:
    #   [all parallel] notify_recommended_school_event(school_entity[school_id]) [in common/utils.py]
        test = 1
    return 0