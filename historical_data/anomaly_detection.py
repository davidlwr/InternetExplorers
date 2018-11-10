import schedule
import time
import datetime
from DAOs import resident_DAO

debug_current_time = datetime.datetime(2018, 9, 28) # NOTE: set to None for production

def job():
    current_time = datetime.datetime.now()
    if debug_current_time:
        current_time = debug_current_time

    sdt = current_time + datetime.timedelta(days=-28)

    # get list of residents to check first
    resident_list = resident_DAO.get_list_of_residents()
    rids = [r['resident_id'] for r in resident_list]
    # print(rids)

    # check for bedroom overstay, temperature and pulse pressure anomalies
    

if not debug_current_time:
    schedule.every().day.at("00:00").do(job)
else:
    job()

while True:
    schedule.run_pending()
    time.sleep(1)
