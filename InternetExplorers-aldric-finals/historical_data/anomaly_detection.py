import schedule
import time
import datetime

debug_time = datetime.datetime(2018, 9, 28)

def job():
    pass

schedule.every().day.at("00:00").do(job)
    
while True:
    schedule.run_pending()
    time.sleep(1)