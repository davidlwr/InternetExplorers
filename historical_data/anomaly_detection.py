import schedule
import time
import datetime
from DAOs import resident_DAO
from sensor_mgmt import overstay_alert

debug_current_time = datetime.datetime(2018, 10, 28) # NOTE: set to None for production

def job():
    current_time = datetime.datetime.now()
    if debug_current_time:
        current_time = debug_current_time
    previous_day_dt = current_time + datetime.timedelta(days=-1)

    sdt = current_time + datetime.timedelta(days=-28)

    # get list of residents to check first
    resident_list = resident_DAO.get_list_of_residents()
    rids = [r['resident_id'] for r in resident_list]
    print("rids: ", rids)

    # check for bedroom overstay, temperature and pulse pressure anomalies
    overstay_dict = overstay_alert.overstay_alert.get_anomalies(rids, sdt, current_time)
    # print("overstay_dict", overstay_dict)
    for rid in rids:
        individual_overstay_dict = overstay_dict[rid]
        print(individual_overstay_dict)
        temp_anomalies = individual_overstay_dict['temp']
        pulse_anomalies = individual_overstay_dict['pulse']
        room_stay_anomalies = individual_overstay_dict['inRoom']
        
        if temp_anomalies:
            print(str(rid) + "'s temp anomalies")
            print(temp_anomalies)
            
        if pulse_anomalies:
            print(str(rid) + "'s pulse anomalies")
            print(pulse_anomalies)
            
        if room_stay_anomalies:
            print(str(rid) + "'s room stay anomalies")
            print(room_stay_anomalies)
        
        
    print("Done one job")
    

if not debug_current_time:
    schedule.every().day.at("00:00").do(job)
else:
    job()

while True:
    print("Entering while loop...")
    schedule.run_pending()
    time.sleep(20) # sleep time longer since this scheduler is aimed at long interval tasks (24 hours)
