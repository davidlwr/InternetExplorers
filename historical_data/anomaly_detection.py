import schedule
import time
import datetime
from DAOs import resident_DAO, anomaly_DAO
from sensor_mgmt import overstay_alert

debug_current_time = datetime.datetime(2018, 9, 29) # NOTE: set to None for production
category_strings = {}
category_strings['temperature'] = "vitals"
category_strings['pulse_pressure'] = "vitals"
category_strings['room_stay'] = "sleep"
category_strings['toilet_usage'] = "nighttoilet"

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
    overstay_dict = overstay_alert.overstay_alert.get_anomalies(rids, sdt, current_time, night_filter=True)
    # print("overstay_dict", overstay_dict)
    for rid in rids:
        individual_overstay_dict = overstay_dict[rid]
        # print(individual_overstay_dict)
        temp_anomalies = individual_overstay_dict['temp']
        pulse_anomalies = individual_overstay_dict['pulse']
        room_stay_anomalies = individual_overstay_dict['inRoom']
        toilet_usage_anomalies = individual_overstay_dict['nbath']
        
        if temp_anomalies:
            print("handling " + str(rid) + "'s temp anomalies")
            # print(temp_anomalies)
            for ta_time, ta_val in temp_anomalies:
                if ta_time.date() == previous_day_dt.date():
                    print("Inserting to db...")
                    # print(ta_time.date())
                    # print(ta_val)
                    desc_text = "Anomalous temperature (" + str(ta_val) + chr(176) + "C) detected!"
                    if ta_val >= overstay_alert.overstay_alert.temperature_max:
                        desc_text = "High temperature (" + str(ta_val) + chr(176) + "C) detected!"
                    elif ta_val <= overstay_alert.overstay_alert.temperature_min:
                        desc_text = "Low temperature (" + str(ta_val) + chr(176) + "C) detected!"
                    try:
                        anomaly_DAO.insert_anomaly(previous_day_dt.strftime("%Y-%m-%d"), rid, category_strings['temperature'], 'Temperature', desc_text, 0)
                    except:
                        print("Exception occurred at temp_anomalies")

        if pulse_anomalies:
            print("handling " + str(rid) + "'s pulse anomalies")
            # print(pulse_anomalies)
            for pa_time, pa_val in pulse_anomalies:
                if pa_time.date() == previous_day_dt.date():
                    print("Inserting to db...")
                    desc_text = "Anomalous pulse pressure (" + str(pa_val) + "mmHg) detected!"
                    try:
                        anomaly_DAO.insert_anomaly(previous_day_dt.strftime("%Y-%m-%d"), rid, category_strings['pulse_pressure'], 'Pulse Pressure', desc_text, 0)
                    except:
                        print("Exception occurred at pulse_anomalies")

        if room_stay_anomalies:
            print("handling " + str(rid) + "'s room stay anomalies")
            # print(room_stay_anomalies)
            for rsa_time, rsa_val in room_stay_anomalies.items():
                if rsa_time.date() == previous_day_dt.date():
                    print("Inserting to db...")
                    desc_text = "Anomalous room activity duration detected"
                    try:
                        anomaly_DAO.insert_anomaly(previous_day_dt.strftime("%Y-%m-%d"), rid, category_strings['room_stay'], 'Room Stay', desc_text, 0)
                    except:
                        print("Exception occurred at room stay anomalies")

        if toilet_usage_anomalies:
            print("handling " + str(rid) + "'s toilet usage anomalies")
            # print(toilet_usage_anomalies)
            for tua_time, tua_val in toilet_usage_anomalies.items():
                if tua_time.date() == previous_day_dt.date():
                    print("Inserting to db")
                    desc_text = "Anomalous night toilet usage detected"
                    try:
                        anomaly_DAO.insert_anomaly(previous_day_dt.strftime("%Y-%m-%d"), rid, category_strings['toilet_usage'], 'Night Toilet Usage', desc_text, 0)
                    except:
                        print("Exception occurred at toilet usage anomalies")


    print("Done one job")


if not debug_current_time:
    schedule.every().day.at("00:00").do(job)
else:
    job()

while True:
    print("Entering while loop...")
    schedule.run_pending()
    time.sleep(20) # sleep time longer since this scheduler is aimed at long interval tasks (24 hours)
