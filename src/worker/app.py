import schedule
import time

# def job():
#     print("I'm working...")

# schedule.every(10).seconds.do(job)
# schedule.every(10).minutes.do(job)
# schedule.every().hour.do(job)
# schedule.every().day.at("10:30").do(job)
# schedule.every(5).to(10).minutes.do(job)
# schedule.every().monday.do(job)
# schedule.every().wednesday.at("13:15").do(job)
# schedule.every().day.at("12:42", "Europe/Amsterdam").do(job)
# schedule.every().minute.at(":17").do(job)

# def job_with_argument(name):
#     print(f"I am {name}")

# schedule.every(10).seconds.do(job_with_argument, name="Peter")

# def notify_starting_soon():
#     print("Notify events that are starting within 1 hour")

# def notify_recommended_events(school_ids):
#     print("Notifying all users recommended events by school_id " + str(school_ids))

# schedule.every(5).minutes.do(notify_starting_soon)
# schedule.every().day.at("1:30", "America/Los_Angeles").do(notify_recommended_events, school_ids=["test_univ"])

# while True:
#     schedule.run_pending()
#     time.sleep(1)


#     from typing import Any
# import asyncio
# from datetime import timedelta, datetime

# async def example_job():
#     test = 1

# # list of jobs and how frequently they should run
# jobs = [
#     ("Example Job", example_job, timedelta(seconds=5))
# ]

# async def main():
#     job_tasks: list[asyncio.Task[Any]] = []
#     job_last_run: list[datetime] = []
#     job_longer_than_delay: list[bool] = []
#     for i, (_, job_func, _) in enumerate(jobs):
#         job_last_run.append(datetime.utcnow())
#         job_tasks.append(asyncio.create_task(job_func()))
#         job_longer_than_delay.append(False)

#     while True:
#         for i, (job_name, job_func, job_delay) in enumerate(jobs):
#             time_since_last_run = datetime.utcnow() - job_last_run[i]
#             if time_since_last_run >= job_delay:
#                 if job_tasks[i].done():
#                     if job_longer_than_delay[i]:
#                         print(f"Job '{job_name}' took {time_since_last_run}, when delay is {job_delay}")
#                         job_longer_than_delay[i] = False
                    
#                     job_last_run[i] = datetime.utcnow()
#                     job_tasks[i] = asyncio.create_task(job_func())
#                 else:
#                     if not job_longer_than_delay[i]:
#                         print(f"Job '{job_name}' is still running after delay of {job_delay}")
#                         job_longer_than_delay[i] = True
#         await asyncio.sleep(1)


# if __name__ == "__main__":
#     print("Running Where2Be jobs")
#     asyncio.run(main())


# from collections import deque
# import random
# import asyncio

# class RunSome:
#     def __init__(self, task_count=5):
#         self.task_count = task_count
#         self.running = set()
#         self.waiting = deque()
        
#     @property
#     def running_task_count(self):
#         return len(self.running)
        
#     def add_task(self, coro):
#         if len(self.running) >= self.task_count:
#             self.waiting.append(coro)
#         else:
#             self._start_task(coro)
        
#     def _start_task(self, coro):
#         self.running.add(coro)
#         asyncio.create_task(self._task(coro))
        
#     async def _task(self, coro):
#         try:
#             return await coro
#         finally:
#             self.running.remove(coro)
#             if self.waiting:
#                 coro2 = self.waiting.popleft()
#                 self._start_task(coro2)
            
# async def main():
#     runner = RunSome()
#     async def rand_delay():
#         rnd = random.random() + 1
#         print("Task started", runner.running_task_count,
#               runner.running_task_count)
#         await asyncio.sleep(rnd)
#         print("Task ended", asyncio.running_task_count,
#               runner.running_task_count)
#     for _ in range(50):
#         runner.add_task(rand_delay())
#     # keep the program alive until all the tasks are done
#     while runner.running_task_count > 0:
#         await asyncio.sleep(0.1)
        
# if __name__ == "__main__":
#     asyncio.run(main())

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

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

        # get_events() title, 

        events = ["test1", "test2"]

        tasks = [send_and_validate_expo_push_notifications(tokens_with_user_id, title, message, extra) ]
        
        # use asyncio.gather to start all tasks in parallel
        await asyncio.gather(*tasks)
        await asyncio.sleep(1)
        
        dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print(f"Event notify complete at {dt_string}")

        await asyncio.sleep(5)

def start_worker():
    loop = asyncio.get_event_loop()
    loop.create_task(worker())
    loop.run_forever()

async def daily_job():
    await run_scraper()

scheduler = AsyncIOScheduler()
scheduler.add_job(daily_job, 'interval', seconds=5) #, start_date='2023-07-25 02:00:00')
scheduler.start()

start_worker()
