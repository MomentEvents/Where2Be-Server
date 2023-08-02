import time
import schedule
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

from worker.notification.tasks import notify_all_events_starting_soon, notify_recommended_events
import os
import json


async def check_events(db_pool):
    async with db_pool.acquire() as connection:
        rows = await connection.fetch("SELECT * FROM events WHERE event_time >= $1", datetime.now())
    return rows

async def run_scraper():
    dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"Scraper run start: at {dt_string}")
    await asyncio.sleep(10)
    dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"Scraper run ended: at {dt_string}")

async def check_and_run_task_if_due(last_run_time, minimum_interval_minutes, task_function):
    current_time = datetime.now()
    difference = current_time - datetime.strptime(last_run_time, "%Y-%m-%dT%H:%M:%S.%f")
    if difference.seconds / 60 > minimum_interval_minutes:
        print("Running task")
        asyncio.create_task(task_function())
    else:
        time_since_last_run = difference.seconds / 60
        print(f"The task ran {time_since_last_run} minutes ago and will not be run now.")

async def worker():
    task_info_path = os.environ.get('TASK_INFO_PATH')
    while True:
        print("Checking events...")
        with open(task_info_path, 'r') as json_file:
            data = json.load(json_file)
        last_run_info = data["notify_all_events_starting_soon"]

        await check_and_run_task_if_due(last_run_info, 1, notify_all_events_starting_soon)

        await asyncio.sleep(10)


def start_worker():
    loop = asyncio.get_event_loop()
    loop.create_task(worker())
    # loop.create_task(notify_recommended_events())
    loop.run_forever()


async def daily_job():
    await run_scraper()

scheduler = AsyncIOScheduler()
# , start_date='2023-07-25 02:00:00')
scheduler.add_job(daily_job, 'interval', seconds=30)
scheduler.add_job(notify_recommended_events, 'interval', seconds=30)
scheduler.start()

start_worker()
