import json
from datetime import datetime
import os


def read_events(file_path):
    events = []
    # Check if the file exists
    if os.path.exists(file_path):
        print("path exists ###########")
        # Read existing data
        with open(file_path, 'r') as file:
            events = json.load(file)

    # with open(file_path, 'r') as file:
    #     for line in file:
    #         if line.strip():  # Ignore empty lines
    #             events.append(json.loads(line))

    # print("first event = ", events[0])
    return events


def count_events_and_find_latest(file_path, key='CreatorID'):
    events = read_events(file_path)

    current_time = datetime.now()

    event_count = {}
    latest_event = {}
    creator = {}

    for event in events:

        id_value = event[key]

        # Convert startingTime to datetime if it's a string
        if isinstance(event['startingTime'], str):
            event_start_time = datetime.fromisoformat(
                event['startingTime'])

            if event_start_time < current_time:
                print(
                    f"The latest event for {id_value} has already occurred: {event}")
                continue

            event['startingTime'] = event_start_time

        event_count[id_value] = event_count.get(id_value, 0) + 1
        creator[id_value] = event["Name"]

        if id_value not in latest_event or event['startingTime'] > latest_event[id_value]['startingTime']:
            latest_event[id_value] = event

    return event_count, latest_event, creator


# Example usage
file_path = 'all_events.json'
event_count, latest_event, creator = count_events_and_find_latest(
    file_path, key='CreatorID')


final_dict = {}
# Print the results
print("Event Count:", event_count)
print("Latest Events:")
for id_value, event in latest_event.items():
    # print(f"{id_value}: {event}")
    final_dict[id_value] = [creator[id_value], event_count[id_value],
                            str(event["startingTime"]), event["Description"]]

# print(final_dict)

# # Write back to the file
# with open("final_json.json", 'w') as file:
#     json.dump(final_dict, file, indent=4)

# Create a list of tuples from final_dict for sorting
sortable_list = []
for id_value, data in final_dict.items():
    count = event_count[id_value]
    sortable_list.append((id_value, count, data))

# Sort the list by event count (second item in each tuple)
sorted_list = sorted(sortable_list, key=lambda x: x[1], reverse=True)

# Convert the sorted list back to a dictionary for JSON serialization
sorted_dict = {item[0]: item[2] for item in sorted_list}

# Print the sorted results
print(sorted_dict)

# Write the sorted results to a JSON file
with open("final_json.json", 'w') as file:
    json.dump(sorted_dict, file, indent=4)
