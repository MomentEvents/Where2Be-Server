import os
import json
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from worker.notification.tasks import notify_all_events_starting_soon, notify_recommended_events, perform_bot_actions

async def retrieve_events(db_pool):
    """
    Function to retrieve events from the database
    """
    async with db_pool.acquire() as connection:
        events = await connection.fetch("SELECT * FROM events WHERE event_time >= $1", datetime.now())
    return events

async def run_scraper():
    """
    Function to run the scraper
    """
    start_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"Scraper started at {start_time}")

    await asyncio.sleep(10)  # simulation of scraping job

    end_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"Scraper ended at {end_time}")

async def execute_task_if_due(last_run_time, min_interval, task):
    """
    Function to check if the task is due to be run
    """
    current_time = datetime.now()
    time_difference = current_time - datetime.strptime(last_run_time, "%Y-%m-%dT%H:%M:%S.%f")
    if time_difference.seconds / 60 > min_interval:
        print("Executing task")
        asyncio.create_task(task())
    else:
        print(f"Task ran {time_difference.seconds / 60} minutes ago. Not executing it now.")

async def task_manager():
    """
    Function to manage tasks
    """
    task_info_path = "./worker/task_info.json"
    while True:
        print("Checking events...")
        with open(task_info_path, 'r') as json_file:
            task_info = json.load(json_file)
        last_run_info = task_info["notify_all_events_starting_soon"]
        await execute_task_if_due(last_run_info, 1, notify_all_events_starting_soon)
        await asyncio.sleep(10)  # sleep before the next check

def initialize_worker():
    """
    Function to initialize the worker
    """
    loop = asyncio.get_event_loop()
    # loop.create_task(task_manager())
    loop.create_task(perform_bot_actions())
    loop.run_forever()

async def daily_scraper():
    """
    Function to run the scraper daily
    """
    await run_scraper()

def main():
    # Instantiate the scheduler
    scheduler = AsyncIOScheduler()

    scheduler.add_job(daily_scraper, 'interval', seconds=120)
    scheduler.add_job(notify_recommended_events, 'interval', seconds=120)
    scheduler.start()
    initialize_worker()


if __name__ == '__main__':
    main()
