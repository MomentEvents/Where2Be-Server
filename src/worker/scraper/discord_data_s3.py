import subprocess
import sys
import glob
import os
import json
import time
from datetime import datetime
# import datefinder
from os import listdir
from os.path import isfile, join
import shutil

import asyncio

from commands.discord_scraper_commands import run_dotnet_guild_and_upload, run_dotnet_channel_and_upload


channel_names = ["event", "announcement", "bullet", "meet", "opportuni",
                 "intern", "week", "social", "advert", "seminar", "mentor", "schedul"]

folder_names = [
    # "data_UIUC_1",
    #             "data_UIUC_2",
    "data_UCB",
    "data_UCSD"]

api_tokens = [
    # "NDMwODQzMTQ1NTU1NjczMDk4.G0lJZK.X1AR_mbUPOtih_Kfj5t-j9Jm4KgfIbI-39Py-I",
    #         "MTAyMjYxMTk3NTcyMjc3ODYyNA.GeUQzv.J3mUSCtQHHGCxk6mMDJShDWPa0Hhef5KK8ujbE",
    "Mjk2ODk1NjY5NDM0NTgwOTkz.G7zTsY.S_NvMLd2V7_9qKckJbmvjFXDwRwYK_kYlVMmmk",
    "MTAyMjYxMTk3NTcyMjc3ODYyNA.GeUQzv.J3mUSCtQHHGCxk6mMDJShDWPa0Hhef5KK8ujbE"]


def get_id_list(curr_dir: str, channel_names: list) -> list:
    # runs through all the json files in the directory
    id_list = []
    file_location_list = []
    all_files = [f for f in os.walk(curr_dir)]
    for file_list in all_files:
        for filename in file_list[2]:
            filename_without_extension, extension = os.path.splitext(filename)
            if extension == ".json" and any(name in filename_without_extension for name in channel_names):
                full_path = os.path.join(curr_dir, filename)
                file_location_list.append(full_path)

                id_list.append(filename.rsplit("[", 1)[1].split("]")[0])

    return file_location_list, id_list


async def request_with_rate_limit_handling(api_token, id, folder_name, key):
    max_tries = 10
    count = 0
    while count < max_tries:
        try:
            # await run_dotnet_and_upload(api_token, id, folder_name, key)
            await run_dotnet_guild_and_upload(api_token, id, folder_name)
            # If successful, break out of the loop
            break
        except Exception as e:  # Change Exception to your specific exception class, if needed
            # Check if it's a rate limit exception
            if 'StatusCode: 429' in str(e):
                # Extract the retry time (you might need a more sophisticated method to get the Retry-After value)
                retry_after = int(e.headers.get('Retry-After', 25))
                await asyncio.sleep(retry_after)
            else:
                # If it's a different kind of exception, perhaps re-raise it or handle it differently
                raise e
        count += 1


def chunked_tasks(data, chunk_size):
    """Yield successive chunk_size chunks from data."""
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


def clean_and_update_keys():
    """
    Cleans up keys in keys.txt and old_keys.txt and updates keys.txt by removing old keys.
    """

    def read_keys_from_file(filename):
        """Utility function to read keys from a file into a set."""
        with open(filename, 'r') as f:
            return set(f.read().splitlines())

    def write_keys_to_file(filename, keys):
        """Utility function to write keys from a set into a file."""
        with open(filename, 'w') as f:
            for key in keys:
                f.write(key + "\n")

    # Step 1 & 2: Read and write back cleaned keys for keys.txt
    current_keys = read_keys_from_file('./keys.txt')
    write_keys_to_file('./keys.txt', current_keys)

    # Step 3 & 4: Read and write back cleaned keys for old_keys.txt
    old_keys = read_keys_from_file('./old_keys.txt')
    write_keys_to_file('./old_keys.txt', old_keys)

    # Remove the old keys from the current keys
    updated_keys = current_keys - old_keys

    # Step 5: Write the updated keys back to keys.txt
    write_keys_to_file('keys.txt', updated_keys)

    print(updated_keys)


async def main():
    tasks = []

    # Read the file, remove duplicates and write it back
    with open('./buffers/data_UCB/guilds.txt', 'r') as f:
        lines = f.readlines()
        unique_lines = set(lines)

    # Convert the set to a list and sort (if necessary)
    sorted_lines = sorted(list(unique_lines))

    # Decide on a chunk size (for example, 50)
    chunk_size = 10

    # For each chunk of lines
    for subset in chunked_tasks(sorted_lines, chunk_size):
        tasks = []
        for line in subset:
            key = line.rstrip('\n')
            # chan_id = line.rsplit("[", 1)[1].split("]")[0]
            tasks.append(request_with_rate_limit_handling(
                api_tokens[0], line, folder_names[0], key))  # change to chan id

        # Now run all tasks for this chunk
        await asyncio.gather(*tasks)
        # break

    # async with sem:
    #     clean_and_update_keys()

sem = asyncio.Semaphore(1)

asyncio.run(main())
