import time
import schedule
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

from worker.notification.tasks import notify_all_events_starting_soon, notify_recommended_events



async def check_events(db_pool):
    async with db_pool.acquire() as connection:
        rows = await connection.fetch("SELECT * FROM events WHERE event_time >= $1", datetime.now())
    return rows


async def notify(event):
    dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"Notification sent for event {event} at {dt_string}")


async def run_scraper():
    dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"Scraper run start: at {dt_string}")
    await asyncio.sleep(10)
    dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"Scraper run ended: at {dt_string}")


async def worker():
    while True:
        print("Checking events...")

        with open('task_info.json', 'r') as json_file:
            data = json.load(json_file)
        last_run_time = data["last_run"]

        current_time = datetime.datetime.now()
        difference = current_time - datetime.datetime.strptime(last_run_time, "%Y-%m-%d %H:%M:%S")
        if difference.seconds // 60 > 5:
            print("The task did not run properly!")
        else:
            print("The task ran properly.")

        dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print(f"Event notify complete at {dt_string}")

        await asyncio.sleep(60)


def start_worker():
    loop = asyncio.get_event_loop()
    # loop.create_task(worker())
    loop.create_task(notify_all_events_starting_soon())
    loop.create_task(notify_recommended_events())
    loop.run_forever()


async def daily_job():
    await run_scraper()

scheduler = AsyncIOScheduler()
# , start_date='2023-07-25 02:00:00')
scheduler.add_job(daily_job, 'interval', seconds=60)
scheduler.start()

start_worker()
