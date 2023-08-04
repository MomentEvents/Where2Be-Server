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


async def execute_task_if_due(last_run_time, min_interval, task_info):
    """
    Function to check if the task is due to be run
    """
    current_time = datetime.now()
    if isinstance(last_run_time, str):
        last_run_time = datetime.strptime(
            last_run_time, "%Y-%m-%dT%H:%M:%S.%f")
    time_difference = current_time - last_run_time
    task, args = task_info  # Unpack the task function and its arguments
    if time_difference.seconds / 60 >= min_interval:
        print("Executing task")
        asyncio.create_task(task(*args))
    else:
        print(
            f"Task ran {time_difference.seconds / 60} minutes ago. Not executing it now.")


async def task_manager():
    """
    Function to manage tasks
    """
    task_info_path = "./worker/task_info.json"
    while True:
        print("Checking events...")
        with open(task_info_path, 'r') as json_file:
            task_info = json.load(json_file)

        last_run_time = task_info.get("notify_all_events_starting_soon")
        if last_run_time is None:
            # execute your task here
            asyncio.create_task(execute_task_if_due(last_run_time=datetime.now(
            ), min_interval=0, task_info=(notify_all_events_starting_soon, [])))
        else:
            asyncio.create_task(execute_task_if_due(
                last_run_time=last_run_time, min_interval=1, task_info=(notify_all_events_starting_soon, [])))

        last_run_time = task_info.get("perform_bot_actions")
        if last_run_time is None:
            # execute your task here
            asyncio.create_task(execute_task_if_due(last_run_time=datetime.now(), min_interval=0, task_info=(
                perform_bot_actions, [str(datetime.now())])))  # the arg needs to be better
        else:
            asyncio.create_task(execute_task_if_due(last_run_time=last_run_time,
                                min_interval=1, task_info=(perform_bot_actions, [last_run_time])))

        await asyncio.sleep(5*60)  # sleep before the next check


def initialize_worker():
    """
    Function to initialize the worker
    """
    loop = asyncio.get_event_loop()
    loop.create_task(task_manager())
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
    scheduler.add_job(notify_recommended_events, 'interval', seconds=5*60)
    scheduler.start()
    initialize_worker()


if __name__ == '__main__':
    main()
