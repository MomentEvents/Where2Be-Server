# import aioboto3
# import os
# import sys
# import asyncio
# from filelock import FileLock
import json
# import aiofiles
# import gc
import boto3

bucket_name = 'discord-data'

# Use the boto3 client instead of resource for this kind of operation
s3_client = boto3.client(
    's3',
    aws_access_key_id='AKIA2IIOOLB6NPZ5O6NI',
    aws_secret_access_key='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',
)

def get_json_from_s3(object_key,bucket_name= 'discord-data'):

    print("JSOMMMMMMM########")
    # # Initialize the S3 client
    # s3 = boto3.client('s3')

    # Retrieve the object
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)

    # Read the object's content
    file_content = response['Body'].read().decode('utf-8')

    # Parse the JSON
    json_content = json.loads(file_content)
    
    return json_content


def create_new_object_key(filepath):
    parts = filepath.split('/')
    folder_name = parts[2].split(' - ')[0].strip()
    cleaned_str = filepath[2:]
    object_key = cleaned_str.replace('/', f'/{folder_name}/', 1)
    return object_key


async def upload_file_to_s3(filepath, object_key, bucket_name):
    session = aioboto3.Session()
    async with session.client('s3') as s3:
        async with aiofiles.open(filepath, 'rb') as file:
            file_content = await file.read()

        # try:
        await s3.put_object(Bucket=bucket_name, Key=object_key, Body=file_content)
        print(f"Uploaded {filepath} to {bucket_name}/{object_key}")
        # except Exception as e:
        #     print(
        #         f"Error uploading {filepath} to {bucket_name}/{object_key}. Error: {e}")
        #     # Handle error accordingly, maybe retry or log for later

        with FileLock("./keys.txt.lock"):
            with open('./keys.txt', 'a') as f:
                f.write(object_key + "\n")

        # Instead of deleting the file here, return the filepath for deletion later
        return filepath


async def upload_channel(object_key):
    parts = object_key.split("/")
    filepath = "../" + "/".join([parts[0], parts[2]])
    print("object_key:", object_key)

    if not os.path.exists(filepath):
        print(f"File {filepath} does not exist.")

        # Adding a lock when writing to ensure synchronization
        with FileLock("./old_keys.txt.lock"):
            with open('./old_keys.txt', 'a') as f:
                f.write(object_key + "\n")

        chan_id = parts[2].rsplit("[", 1)[1].split("]")[0]
        folder_path = "./" + parts[0]
        matched_files = [f for f in os.listdir(folder_path) if chan_id in f]

        if matched_files:
            filepath = os.path.join(folder_path, matched_files[0])
            print(f"Found file {filepath} with channel ID in its name.")
            # Assuming this function doesn't require async adaptation
            object_key = create_new_object_key(filepath)
            print("new_object_key:", object_key)
        else:
            print(
                f"No files with channel ID {chan_id} found in the directory {folder_path}.")

        file = await upload_file_to_s3(filepath, object_key, bucket_name)

        os.remove(file)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def upload_guild_to_s3(buffer_folder, chunk_size=5):
    files = [f for f in os.listdir(buffer_folder) if f.endswith('.json')]

    upload_tasks = []
    successfully_uploaded_files = []

    for filename in files:
        parts = filename.split(' - ', 1)
        object_key = "data_UCB/" + f"{parts[0]}/{filename}"
        filepath = "/Users/chiragrastogi/Dev/Moment_app/Where2Be-Server/src/worker/scraper/buffers/data_UCB/" + filename

        task = asyncio.create_task(upload_file_to_s3(
            filepath, object_key, bucket_name))
        upload_tasks.append(task)

    MAX_RETRIES = 20
    for chunk in chunks(upload_tasks, chunk_size):
        retries = 0
        while retries < MAX_RETRIES:
            try:
                results = await asyncio.gather(*chunk)
                successfully_uploaded_files.extend(results)
                break
            except BrokenPipeError:
                retries += 1
                if retries == MAX_RETRIES:
                    print(
                        f"Failed to process chunk after {MAX_RETRIES} retries.")
            await asyncio.sleep(15)

    print("successfully_uploaded_files", successfully_uploaded_files)
    unique_files = set(successfully_uploaded_files)

    # Delete the successfully uploaded files
    for file in unique_files:
        async with file_delete_lock:
            if os.path.exists(file):  # Ensure file exists before trying to delete
                os.remove(file)

    # Free up memory after processing
    del unique_files
    del successfully_uploaded_files
    gc.collect()


def download_from_s3(object_key):
    s3_response_object = s3.get_object(Bucket=bucket_name, Key=object_key)
    object_content = s3_response_object['Body'].read()

    # Load the JSON content
    json_content = json.loads(object_content)

    # Now json_content is a dictionary containing the data
    print(json_content)

    file_path = "/Users/chiragrastogi/Dev/Moment_app/Where2Be-Server/src/worker/output.json"

    # Write the JSON data to the file
    with open(file_path, 'w') as json_file:
        json.dump(json_content, json_file, indent=4)

# # Create a lock for file deletion
# file_delete_lock = asyncio.Lock()

def main():
    # if len(sys.argv) < 2:
    #     print("Please provide the object key as an argument.")
    #     sys.exit(1)

    # object_key = sys.argv[1]

    # Running the asynchronous upload_to_s3 function
    asyncio.run(upload_guild_to_s3(
        "/Users/chiragrastogi/Dev/Moment_app/Where2Be-Server/src/worker/scraper/buffers/data_UCB"))



if __name__ == "__main__":
    main()
