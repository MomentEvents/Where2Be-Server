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

def notify_starting_soon():
    print("Notify events that are starting within 1 hour")

def notify_recommended_events(school_ids):
    print("Notifying all users recommended events by school_id " + str(school_ids))

schedule.every(5).minutes.do(notify_starting_soon)
schedule.every().day.at("1:30", "America/Los_Angeles").do(notify_recommended_events, school_ids=["test_univ"])

while True:
    schedule.run_pending()
    time.sleep(1)