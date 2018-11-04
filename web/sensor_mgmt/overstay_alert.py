from __future__ import division
import datetime, os, sys, time, collections
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from itertools import islice, count
import numpy as np
from numpy import linspace, loadtxt, ones, convolve
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import style
style.use('fivethirtyeight')

if __name__ == '__main__': sys.path.append("..")
if __name__ == '__main__': 
    from JuvoAPI import JuvoAPI
else: 
    from sensor_mgmt.JuvoAPI import JuvoAPI
from Entities.sysmon_log import Sysmon_Log
from Entities.sensor_log import Sensor_Log
from DAOs.connection_manager import connection_manager
from DAOs.sensor_DAO import sensor_DAO
from DAOs.sysmon_log_DAO import sysmon_log_DAO
from DAOs.sensor_log_DAO import sensor_log_DAO
from DAOs.shift_log_DAO import shift_log_DAO

class overstay_alert(object):
    """
    NOTE: IF THIS IS THE ONLY THING YOU READ: SEE overstay_alert.get_anomalies(rids, sdt, edt, mm_pure=True, tm_pure=True, window=7, sigma=2)\
            - Using the default values for mm_pure and tm_pure is fine
            - Method is also ment to be run after the day itself. say you want to check 10/10/2018, wait until 11/10/2018 00:00:00, then run with edt = 10/10/2018

    ------  POINTWISE DETECTION:
                2 main methods for checking, given an exact time, how long resident has been in his/her room/toilet
                NOTE: in room only works with residents with a main door sensor!!
                    - check_in_room_mdoor() and check_in_toilet()

    ------  SUMMARY DETECTION METHODS:
                1 main method for checking given a date, 3 things >> `time_in_room`, `time_in_toilet`, `nbath_visits`
                - check_activities_by_date()
                NOTE: there are 4 sub algos that deal with the different sensor sets. i.e. Does resident have toilet door sensor?
                NOTE: Due to this, without door sensors, an estimate is given using the motion sensors only
                        - Time in Toilet, if set to use door sensor also (tm_pure=False). Will have greatly differing values from those with door sensors
                        - THis is due to the residents wandering in and out of the toilet, and the 4 minute timeout of motion sensors

    ------  MOVING AVERAGE ANOMALY DETECTION
                Contains 2 anomaly detection. 1 using moving average.
                Also contains a method for plotting out a graph based on anomalies found
    """
    MOTION_TIMEOUT = 4   # mins. motion sensor minutes of inactivity before sending 0 to close off 225 event
    DOOR_CLOSE = 0
    DOOR_OPEN  = 255

    MOTION_START = 255
    MOTION_END   = 0

    # THRESHOLDS TEMP and PULSE
    temperature_max 		= 37.6
    temperature_min 		= 35.5
    pulse_pressure_max 	    = 62.5        # https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2710466/
    
    # RETURN CODES:
    NO_MAIN_DOOR = -1    # Unable to run algo, as no main door sensor found
    DC_MAIN_DOOR = -2    # Unable to run algo, main doow is down. NOTE: no real action needed, CHECKWARN should already be sent
    INVALID_SSET = -3    # Unable to run algo, due to lack of combination of sensors

    @staticmethod
    def extract_sensors(sensors):
        '''
        Input 
        sensors (dict) -- {"uuid": [pStart, pEnd, type, location, juvo target]} 
        NOTE: Give only current owners

        Returns dict. value of either uuid or juvo target id
        default {"mDoor":None, "mMotion":None, 'tDoor':None, 'tMotion':None, 'juvo':None}
        '''
        sensor_dict = {"mDoor":None, "mMotion":None, 'tDoor':None, 'tMotion':None, 'juvo':None}

        for uuid,ls in sensors.items():
            t = ls[0]
            l = ls[1]
            jtarget = ls[2]
            if t == "door" and l == "bedroom":   sensor_dict["mDoor"] = uuid
            elif t == "motion" and l == "bedroom": sensor_dict["mMotion"] = uuid
            elif t == "door" and l == "toilet":    sensor_dict["tDoor"] = uuid
            elif t == "motion" and l == "toilet":  sensor_dict["tMotion"] = uuid
            elif t == "bed sensor" and l == "bed": sensor_dict["juvo"] = jtarget
            else: print("Unable to match sensor?? ", uuid, ls)
        return sensor_dict

    # POINTWISE DETECTION ======================================
    @staticmethod
    def check_isolated_door_motion(last_door, last_motions, now):
        '''
        Isolated situation where there is 1 door and 1 motion sensor

        Returns int. 0 meaning resident not in as of now
        '''
        sec_diff = (now - last_door.recieved_timestamp).total_seconds()

        if len(last_motions) > 0:       # last motion found
            for mlog in last_motions:   # Check if any was a 225, start motion, reading after door closed

                # Check 1 >> motion start after door close
                if mlog.event == 225 and mlog.recieved_timestamp > last_door.recieved_timestamp:
                    return sec_diff

                # Check 2 >> motion refresh after door close. event > 5 min (timeout)
                if mlog.event == 0 and mlog.recieved_timestamp - timedelta(minutes=overstay_alert.MOTION_TIMEOUT) > last_door.recieved_timestamp:
                    return sec_diff

        # Check 3 >> open motion event >> if doorClose to now > MOTION_TIMEOUT then motion event refreshed. resident is in 
        #   motion 225 began before door close. ensured due to above if conditions / checks
        if len(last_motions) == 1 and last_motions[0].event == 225 and sec_diff/60 > overstay_alert.MOTION_TIMEOUT:
            return sec_diff

        # else cannot be sure anyone is in room
        return 0

    @staticmethod
    def check_in_room_mdoor(rid, sdict=None, sudo_now=None):
        '''
        Returns:
        An int that can either be a return code or number of seconds person has been in room ()
            - For -2, and -1, see RETURN CODES
            - Else interpret int as number of seconds in room

         NOTE: IDEALLY this would take into account situation when door is open but resident is in the room.
         HOWEVER we are using this to further validate if resident is in the toilet so we will return IN ROOM status when we are really sure
        '''
        # Define now
        now = datetime.datetime.now() if sudo_now == None else sudo_now  

        # List of currently owned sensors   
        if sdict == None: 
            sensors = sensor_DAO.get_owned_sensors(rid=rid, dt=now)
            sdict = overstay_alert.extract_sensors(sensors=sensors)

        # Check for main door
        mdoor_uuid = sdict["mDoor"]
        if mdoor_uuid == None: return overstay_alert.NO_MAIN_DOOR        

        # Get last record of main door close
        logs = sensor_log_DAO.get_last_logs(uuid=mdoor_uuid, dt=now)
        if len(logs) == 0: return 0    # Deals with no logs found

        last_mdoor = logs[0]
        secs_since_last_mdoor = (now - last_mdoor.recieved_timestamp).total_seconds()

        # DEAL WITH ERROR PERIODS
        # NOTE: we can only detect in general when door is down: by date ONLY
        #       Therefore we can only do a rough sanity check >> If last door log was > 1 day ago. period between then and now will be down
        #       In this case we will just return error code DC_MAIN_DOOR: Indicating that the sensor is untrusted and may be down. CHECKWARN'd
        if (now - last_mdoor.recieved_timestamp).total_seconds() > (60 * 60 * 24): return overstay_alert.DC_MAIN_DOOR

        # Else check if door close event
        if last_mdoor.event == overstay_alert.DOOR_CLOSE:    # Door close >> Check for ANY sensor trigger inside room to validate person inside

            # Check if any MAIN MOTION
            mmotion_uuid = sdict['mMotion']                            
            if mmotion_uuid != None:    
                logs =  sensor_log_DAO.get_last_logs(uuid=mmotion_uuid, dt=now, limit=2) # Get last logs
                check = overstay_alert.check_isolated_door_motion(last_door=last_mdoor, last_motions=logs, now=now)
                if check > 0: return check

            # Check if any TOILET MOTION
            tmotion_uuid = sdict['tMotion']
            if tmotion_uuid != None:   
                logs =  sensor_log_DAO.get_last_logs(uuid=tmotion_uuid, dt=now, limit=2)  # Get last logs
                check = overstay_alert.check_isolated_door_motion(last_door=last_mdoor, last_motions=logs, now=now)
                if check > 0: return check

            # Check if any TOILET DOOR  >> any state change
            tdoor_uuid = sdict['tDoor']
            if tdoor_uuid != None:
                logs =  sensor_log_DAO.get_last_logs(uuid=tdoor_uuid, dt=now)                    # Get last log
                if len(logs) > 0 and logs[0].recieved_timestamp > last_mdoor.recieved_timestamp: # If last log found and after door close
                    return secs_since_last_mdoor

            # Check if any JUVO      >> Get juvo heartrates from last close -- now if any != 0. someone was on the bed
            jtarget = sdict['juvo']
            if jtarget != None:
                vitals_json = JuvoAPI.get_target_vitals(target=jtarget, start_time=last_mdoor.recieved_timestamp, end_time=now)
                heart_pd,_  = JuvoAPI.extract_heart_breath_from_vitals(json=vitals_json)
                if len(heart_pd.index) > 0:
                    heart_rates = heart_pd.query("heart_rate > 0") 
                    if len(heart_rates.index) > 0: 
                        return secs_since_last_mdoor

        return 0

    @staticmethod
    def check_in_toilet(rid, sudo_now=None):
        '''
        if return < 0: see error codes
        else return = seconds person has been in toilet

        NOTE: This method is only sensitive to >5mins, it cannot detect toilet stays of <5mins
        '''
        # Define now
        now = datetime.datetime.now() if sudo_now == None else sudo_now  
         
        # List of currently owned sensors      
        sensors = sensor_DAO.get_owned_sensors(rid=rid, dt=now)
        sdict = overstay_alert.extract_sensors(sensors=sensors)
        uuids = [uuid for k,uuid in sdict.items() if uuid != None]

        tdoor_uuid   = sdict['tDoor']
        tmotion_uuid = sdict['tMotion']
        mmotion_uuid = sdict['mMotion']
        
        # Check 1 >> Toilet door found, combine with toilet motion 
        if tdoor_uuid != None and tmotion_uuid != None:
            logs = sensor_log_DAO.get_last_logs(uuid=tdoor_uuid, dt=now)         # Get last record of toilet door close
            last_tdoor = logs[0] if len(logs) != 0 else None
            # print("IN Check 1... now, last_tdoor", now, last_tdoor.recieved_timestamp)

            # ghetto check for door validity. Ensure didnt happen >24 hrs ago
            if last_tdoor != None and last_tdoor.event == overstay_alert.DOOR_CLOSE and (now - last_tdoor.recieved_timestamp).total_seconds() < (60 * 60 * 24):
                logs = sensor_log_DAO.get_last_logs(uuid=tmotion_uuid, dt=now)         # Get last record of toilet motion
                last_tmotion = logs[0] if len(logs) != 0 else None
                # print("\t", last_tmotion.recieved_timestamp)
                if last_tmotion != None:
                    # print("IN Check 1.1... last_tmotion", last_tmotion)
                    check = overstay_alert.check_isolated_door_motion(last_door=last_tdoor, last_motions=logs, now=now)
                    if check >= 0: return check


        # Check 2 >> run algo based on movement in room. MAIN DOOR, MAIN MOTION, TOILET MOTION found
        if mmotion_uuid != None and tmotion_uuid != None:
            # print("in Check 2... ", now)
            # Get last instances of 225 of both motion, use this to track movement
            t_mlogs = sensor_log_DAO.get_last_logs(uuid=tmotion_uuid, dt=now, limit=2)
            m_mlogs = sensor_log_DAO.get_last_logs(uuid=mmotion_uuid, dt=now, limit=2)
            # print("\ttoilet m logs: ", [(x.recieved_timestamp, x.event) for x in t_mlogs])
            # print("\tmain m logs:   ", [(x.recieved_timestamp, x.event) for x in m_mlogs])

            # Check 2.1 >> both are event == 0, closed motion events
            # print("bef Check 2.1")
            if len(t_mlogs) == 2 and len(m_mlogs) == 2:
                if t_mlogs[0].event == 0 and m_mlogs[0].event == 0:            # Latest is:      0   / close
                    if t_mlogs[1].event == 225 and m_mlogs[1].event == 225:    # 2nd latest is:  225 / start
                        # Resident can be considered to be in the place of the sensor with the latest log
                        if t_mlogs[0].recieved_timestamp > m_mlogs[0].recieved_timestamp: 
                            return (now - (t_mlogs[0].recieved_timestamp - timedelta(minutes=5))).total_seconds()

            
            if len(t_mlogs) > 0 and len(m_mlogs) > 0:
                # Check 2.2 >> 1 event is closed, 1 is open
                if t_mlogs[0].event == 225 and m_mlogs[0].event == 0:    # Toilet open, Main closed
                    return (now - (m_mlogs[0].recieved_timestamp - timedelta(minutes=5))).total_seconds()

                # Check 2.3 >> both events open NOTE: WITH THIS SITUATION WE cannot be certain where person is. real ghetto
                if t_mlogs[0].event == 225 and m_mlogs[0].event == 225:
                    if t_mlogs[0].recieved_timestamp > m_mlogs[0].recieved_timestamp:
                        return (now - t_mlogs[0].recieved_timestamp).total_seconds()

        return 0

    # SUMMARY DETECTION METHODS ========================================
    @staticmethod
    def check_activities_by_date(rid, sdt, edt, mm_pure=False, tm_pure=True):
        """  Checkes values of `time_in_room`, `time_in_bath`, `nbath_visits` per day for a specific resident
        INPUTS:
        -----
                 rid (int) -- resident ID
                 sdt (datetime) -- start datetime
                 edt (datetime) -- end datetime
                 tm_pure (bool) -- If true, uses algo that evaluates toilet activity based solely on motion sensors.

                 * Because some residents have toilet door sensors, allowing us to be more accurate in the time evaluations here
                 ** Meaning that the values are quite different, as the residents enjoy wandering into the toilets randomly, inflating the values

        RETURN:
        -----
                ret_list (list) -- [ {"date":curr_sdt, "secs_room":time_in_room, "secs_bath":time_in_bath, "nvisit_bath":nvisits_bath},
                                      ...
                                     {"date":curr_sdt, "secs_room":time_in_room, "secs_bath":time_in_bath, "nvisit_bath":nvisits_bath},
                                   ]
        """
        # List of currently owned sensors      
        sensors = sensor_DAO.get_owned_sensors(rid=rid, dt=edt)
        sdict = overstay_alert.extract_sensors(sensors=sensors)
        uuids = [uuid for k,uuid in sdict.items() if uuid != None]

        md_uuid = sdict['mDoor']
        mm_uuid = sdict['mMotion']
        td_uuid = sdict['tDoor']
        tm_uuid = sdict['tMotion']

        # print(f"RID {rid}")
        # print("\t main w used" if md_uuid != None and mm_pure == False else "\t main wo used")
        # print("\t bath w used" if td_uuid != None and tm_pure == False else "\t bath wo used")

        # Get all sensor logs
        logs_dt = sensor_log_DAO.get_all_logs()

        curr_sdt = sdt.replace(hour=0, second=0, minute=0, microsecond=0)
        edate    = edt.replace(hour=0, second=0, minute=0, microsecond=0)

        # Loop between dates and get summary statistics
        ret_list = []
        while curr_sdt <= edate:
            curr_edt = curr_sdt.replace(hour=23, minute=59, second=59)

            # Summary values
            time_in_room = 0
            time_in_bath = 0
            nvisits_bath = 0

            # Pull out all logs within the current date
            curr_logs = logs_dt[(logs_dt['recieved_timestamp'] >= curr_sdt) & (logs_dt['recieved_timestamp'] <= curr_edt)]
            curr_logs = curr_logs[curr_logs['uuid'].isin(uuids)]
            curr_logs.sort_values(by='recieved_timestamp', ascending=True, inplace=True)

            # Get time in main room
            if md_uuid != None and mm_pure == False:
                time_in_room = overstay_alert.sub_room_w_door(curr_logs, sdict, curr_sdt, curr_edt)
            else:
                time_in_room = overstay_alert.sub_room_wo_door(curr_logs, sdict, curr_sdt, curr_edt)

            # Get time in toilet
            if td_uuid != None and tm_pure == False:
                time_in_bath, nvisits_bath = overstay_alert.sub_bath_w_door(curr_logs, sdict, curr_sdt, curr_edt)
            else:
                time_in_bath, nvisits_bath = overstay_alert.sub_bath_wo_door(curr_logs, sdict, curr_sdt, curr_edt)

            # Add summary values to ret_dict
            ret_list.append({"date":curr_sdt, "secs_room":time_in_room, "secs_bath":time_in_bath, "nvisit_bath":nvisits_bath})

            # Increment curr_date
            curr_sdt += timedelta(days=1)

        return ret_list
             
    @staticmethod
    def sub_room_w_door(curr_logs, sdict, curr_sdt, curr_edt):
        # Summary values
        time_in_room = 0

        # Iterate logs in ascending datetime order. Generate summary values >> Greedy algo
        prev_md = None
        prev_tm = None
        prev_mm = None
        for i in range(0, len(curr_logs)) :
            row = curr_logs.iloc[i]

            # If Door
            if row.uuid == sdict["mDoor"]:

                # Deal with situation where door close was before the sdt
                if type(prev_md) == type(None): 
                    if row.event == overstay_alert.DOOR_OPEN:
                        # print(f"\t Adding from first dopen: {row.recieved_timestamp} \t {curr_sdt}")
                        time_in_room += (row.recieved_timestamp - curr_sdt).total_seconds()

                # If current door event is OPEN and previous door event is CLOSE
                elif (row.event == overstay_alert.DOOR_OPEN and prev_md.event == overstay_alert.DOOR_CLOSE):
                    # Check if any motion in room while door was closed. If yes, then take this as in room
                        if type(prev_tm) != type(None): 
                            if prev_tm.recieved_timestamp > prev_md.recieved_timestamp: 
                                # print(f"\t Adding from prev tm: {row.recieved_timestamp} \t {prev_md.recieved_timestamp}")
                                time_in_room += (row.recieved_timestamp - prev_md.recieved_timestamp).total_seconds()

                        elif type(prev_mm) != type(None): 
                            if prev_mm.recieved_timestamp > prev_md.recieved_timestamp:
                                # print(f"\t Adding from prev mm: {row.recieved_timestamp} \t {prev_md.recieved_timestamp}")
                                time_in_room += (row.recieved_timestamp - prev_md.recieved_timestamp).total_seconds()

                prev_md = row

            # If toilet Motion                
            elif row.uuid == sdict["tMotion"]: prev_tm = row
            # If main Motion
            elif row.uuid == sdict["mMotion"]: prev_mm = row
            
        # Deal with trailing status
        #   Final main door == closed
        if type(prev_md) != type(None):
            if prev_md.event == overstay_alert.DOOR_CLOSE:
                add_last = False
                if type(prev_tm) != type(None):     # Check for any motion inside toilet motion
                    if prev_tm.recieved_timestamp > prev_md.recieved_timestamp:  
                        add_last = True

                if type(prev_mm) != type(None):   # Check for any motion inside main motion
                    if prev_mm.recieved_timestamp > prev_md.recieved_timestamp:  
                        add_last = True
                
                if add_last:
                    # print(f"\t Adding last: {curr_edt} \t {prev_md.recieved_timestamp}")
                    time_in_room += (curr_edt - prev_md.recieved_timestamp).total_seconds()

        return time_in_room

    @staticmethod
    def sub_room_wo_door(curr_logs, sdict, curr_sdt, curr_edt):
        # Summary values
        time_in_room = 0

        # Iterate logs in ascending datetime order. Generate summary values >> Greedy algo
        # Find start of a motion event, search for end, if encounter another motion start (of other sensor), look for that end instead. Use abs start and end to take time in room 
        first_motion_found = False
        uuid_searching_end = None
        i = 0
        # print(f"BEGINNING >> curr i={i}, len of curr logs = {len(curr_logs)}")
        while i < len(curr_logs):
            
            row = curr_logs.iloc[i]

            # ALSO POTENTIALY BUGGY, but not by alot. since data suggest residents dont really sleep for a long period of time. More like they nap alot
            if first_motion_found == False and row.recieved_timestamp < curr_sdt.replace(hour=6) and (row.uuid == sdict['mMotion'] or row.uuid == sdict['mMotion']):
                # print(f"\t Adding from Head: {row.recieved_timestamp} \t {curr_sdt}")
                time_in_room += (row.recieved_timestamp - curr_sdt).total_seconds() 
                first_motion_found = True

            # If its a start of a motion event, look for the end
            elif row.uuid == sdict['mMotion'] or row.uuid == sdict['tMotion'] and row.event == overstay_alert.MOTION_START:
                # print(f"\t STARTING LOOK AHEAD at i = {i} ==========")
                uuid_searching_end = row.uuid

                # Look forward
                for j in range(i+1, len(curr_logs)):
                    future_row = curr_logs.iloc[j]

                    if future_row.uuid == uuid_searching_end and future_row.event == overstay_alert.MOTION_END:
                        # print(f"\t Adding from future search: {future_row.recieved_timestamp} \t {row.recieved_timestamp- timedelta(minutes=overstay_alert.MOTION_TIMEOUT)}")
                        time_in_room += (future_row.recieved_timestamp - row.recieved_timestamp - timedelta(minutes=overstay_alert.MOTION_TIMEOUT)).total_seconds()

                        # Skip i ahead to after j
                        uuid_searching_end = None    # Set to None when search ends
                        # print(f"\t Skipping i at j {j} >> before {i} , after {i + (j-i)}")
                        i += j - i 
                        # print(f"\t checking after skip... {i}")
                        break

                    # If another motion sensor starts within the room, look for its end instead
                    elif (future_row.uuid  == sdict['mMotion'] or future_row.uuid == sdict['mMotion']) and future_row.event == overstay_alert.MOTION_START:
                        # print(f"\t Found new to look ahread: prev={uuid_searching_end}, new={future_row.uuid}")
                        uuid_searching_end = future_row.uuid

                    # Tail end, open seach, but we hit edt >> POTENTIALLY BUGGY AF
                    elif j == len(curr_logs) - 1: 
                        # print(f"\t Adding from tail: {curr_edt} \t {row.recieved_timestamp}")
                        time_in_room += (curr_edt - row.recieved_timestamp).total_seconds()

                        uuid_searching_end = None    # Set to None when search ends
                        # print(f"\t Skipping i at j {j} >> before {i} , after {i + (j-i)}")
                        i += j - i 
                        # print(f"\t checking after skip... {i}")
                        break

                # print("\t EXITING LOOK AHEAD ====================")
            # print(f"\t i incrementing from {i} to {i+1}")
            i += 1  # Increment counter
        return time_in_room

    @staticmethod
    def sub_bath_w_door(curr_logs, sdict, curr_sdt, curr_edt):
        # Summary values
        time_in_bath = 0
        nvisits_bath = 0

        # Iterate logs in ascending datetime order. Generate summary values >> Greedy algo
        prev_td = None
        prev_tm = None
        prev_mm = None
        for i in range(0, len(curr_logs)) :
            row = curr_logs.iloc[i]

            # If Toilet Door
            if row.uuid == sdict["tDoor"]:

                # Deal with situation where door close was before the sdt
                if type(prev_td) == type(None): 
                    if row.event == overstay_alert.DOOR_OPEN:
                        time_in_bath += (row.recieved_timestamp - curr_sdt).total_seconds()
                        nvisits_bath += 1

                # If current door event is OPEN and previous door event is CLOSE
                elif (row.event == overstay_alert.DOOR_OPEN and prev_td.event == overstay_alert.DOOR_CLOSE):
                    # Check if any motion in room while door was closed. If yes, then take this as in room
                        if type(prev_tm) != type(None): 

                            # Motion start after door close 
                            if prev_tm.event == overstay_alert.MOTION_START and prev_tm.recieved_timestamp > prev_td.recieved_timestamp: 
                                time_in_bath += (row.recieved_timestamp - prev_td.recieved_timestamp).total_seconds()
                                nvisits_bath += 1

                            # Motion close after door close and before door open
                            elif prev_tm.event == overstay_alert.MOTION_END and prev_tm.recieved_timestamp - timedelta(minutes=overstay_alert.MOTION_TIMEOUT) < row.recieved_timestamp:
                                time_in_bath += (row.recieved_timestamp - prev_td.recieved_timestamp).total_seconds()
                                nvisits_bath += 1

                            # Motion start before door close, within a 4 minute window
                            elif prev_tm.event == overstay_alert.MOTION_START and prev_tm.recieved_timestamp < prev_td.recieved_timestamp - timedelta(minutes=overstay_alert.MOTION_TIMEOUT):
                                # last mian room motion was start and was before door close
                                if type(prev_mm) != type(None):
                                    if prev_mm.event == overstay_alert.MOTION_START and prev_mm.recieved_timestamp < prev_td.recieved_timestamp:
                                        time_in_bath += (row.recieved_timestamp - prev_td.recieved_timestamp).total_seconds()
                                        nvisits_bath += 1

                                    # last main room motion was end, and was refreshed before main door closed
                                    elif prev_mm.event == overstay_alert.MOTION_END: 
                                        if prev_mm.recieved_timestamp - timedelta(minutes=overstay_alert.MOTION_TIMEOUT) < prev_td.recieved_timestamp:
                                            time_in_bath += (row.recieved_timestamp - prev_td.recieved_timestamp).total_seconds()
                                            nvisits_bath += 1
                prev_td = row

            # If toilet Motion                
            elif row.uuid == sdict["tMotion"]: prev_tm = row
            elif row.uuid == sdict["mMotion"]: prev_mm = row
                
            # Deal with trailing status
            #   Final main door == closed
            if type(prev_td) != type(None):
                if prev_td.event == overstay_alert.DOOR_CLOSE:
                    if type(prev_tm) != type(None):     # Check for any motion inside toilet motion
                        if prev_tm.event == overstay_alert.MOTION_END and prev_tm.recieved_timestamp > (prev_td.recieved_timestamp + timedelta(minutes=overstay_alert.MOTION_TIMEOUT)):  
                            time_in_bath += (curr_edt - prev_td.recieved_timestamp).total_seconds()
                            nvisits_bath += 1
                        elif prev_tm.event == overstay_alert.MOTION_START and prev_tm.recieved_timestamp > prev_td.recieved_timestamp:
                            time_in_bath += (curr_edt - prev_td.recieved_timestamp).total_seconds()
                            nvisits_bath += 1

        return time_in_bath, nvisits_bath

    @staticmethod
    def sub_bath_wo_door(curr_logs, sdict, curr_sdt, curr_edt):
        # Summary values
        time_in_bath = 0
        nvisits_bath = 0

        # Iterate logs in ascending datetime order. Generate summary values >> Greedy algo
        prev_tm = None
        for i in range(0, len(curr_logs)) :
            row = curr_logs.iloc[i]

            # If toilet Motion                
            if row.uuid == sdict["tMotion"]:
                # EVENT START
                if row.event == overstay_alert.MOTION_START: 
                    nvisits_bath += 1

                    # Motion log 225 then 225?? treat previous start as being 4 mins long
                    if type(prev_tm) != type(None):
                        if prev_tm.event == overstay_alert.MOTION_START: 
                            time_in_bath += 60 * overstay_alert.MOTION_TIMEOUT

                # EVENT END
                if row.event == overstay_alert.MOTION_END:
                    if type(prev_tm) != type(None):
                        if prev_tm.event == overstay_alert.MOTION_START:
                            event_length = (row.recieved_timestamp - prev_tm.recieved_timestamp - timedelta(minutes=overstay_alert.MOTION_TIMEOUT)).total_seconds()
                            time_in_bath += event_length

                prev_tm = row
            
        # Deal with trailing status
        #   Final toilet motion open
        if type(prev_tm) != type(None):
            if prev_tm.event == overstay_alert.MOTION_START:
                time_in_bath += (curr_edt - prev_tm.recieved_timestamp).total_seconds()

        return time_in_bath, nvisits_bath

    # SUB FORMATTING HELPER METHODS =============================
    @staticmethod
    def dt_diff(sdt, edt):
        '''
        Takes in two datetimes and returns difference (sdt,edt) in years, hours, mins, and seconds
        {'years': 0,'hours': 0, 'minutes': 0, 'seconds': 0}
        '''
        diff = relativedelta(dt1=edt, dt2=sdt)
        return {'years':diff.years, 'hours':diff.hours, 'minutes':diff.minutes, 'seconds':diff.seconds}

    @staticmethod
    def parse_sec_diff(secs):
        '''
        Returns secs in terms of years, hours, mins, and seconds
        {'years': 0,'hours': 0, 'minutes': 0, 'seconds': 0}
        '''
        diff = relativedelta(seconds=secs)
        return {'years':diff.years, 'hours':diff.hours, 'minutes':diff.minutes, 'seconds':diff.seconds}

    # MOVING AVERAGE ANOMALY DETECTION ===========================
    @staticmethod
    def moving_average(data, window_size):
        """ Computes moving average using discrete linear convolution of two one dimensional sequences.
        Args:
        -----
                data (pandas.Series): independent variable
                window_size (int): rolling window size

        Returns:
        --------
                ndarray of linear convolution

        References:
        ------------
        [1] Wikipedia, "Convolution", http://en.wikipedia.org/wiki/Convolution.
        [2] API Reference: https://docs.scipy.org/doc/numpy/reference/generated/numpy.convolve.html

        """
        # window_kernel = np.ones(int(window_size))/float(window_size)
        # convolved_moving_avg = np.convolve(data, window_kernel, 'same')
        # Due to how np deals with kernel shifting over edges, the ends seem to be amplifying trends; Pandas seems to do it better 

        pandas_moving_avg = data.rolling(window=window_size, center=False).mean()

        # print("convolved_moving average", convolved_moving_avg)
        # print("pandas_moving average   ", pandas_moving_avg)
        return pandas_moving_avg

    @staticmethod
    def explain_anomalies(x, y, window_size, sigma=1.0):
        """
         Helps in exploring the anamolies using stationary standard deviation
        Args:
        -----
            y (pandas.Series): independent variable
            window_size (int): rolling window size
            sigma (int): value for standard deviation

        Returns:
        --------
            a dict (dict of 'standard_deviation': int, 'anomalies_dict': (index: value))
            containing information about the points indentified as anomalies

        """
        avg = overstay_alert.moving_average(y, window_size).tolist()
        residual = y - avg
        # Calculate the variation in the distribution of the residual
        std = np.std(residual)
        return {'standard_deviation': round(std, 3),
                'anomalies_dict': collections.OrderedDict([(x[index], y_i) for index, y_i, avg_i in zip(count(), y, avg)
                                                                        if (y_i > avg_i + (sigma*std)) | (y_i < avg_i - (sigma*std))])}

    @staticmethod
    def explain_anomalies_rolling_std(x, y, window_size, sigma=2.0):
        """ Helps in exploring the anamolies using rolling standard deviation
        Args:
        -----
            y (pandas.Series): independent variable
            window_size (int): rolling window size
            sigma (int): value for standard deviation

        Returns:
        --------
            a dict (dict of 'standard_deviation': int, 'anomalies_dict': (index: value))
            containing information about the points indentified as anomalies
        """
        avg = overstay_alert.moving_average(y, window_size)
        avg_list = avg.tolist()
        residual = y - avg
        # Calculate the variation in the distribution of the residual
        testing_std       = residual.rolling(window=window_size, center=False).std() # DEPRECIATED pd.rolling_std(residual, window_size) 
        testing_std_as_df = pd.DataFrame(testing_std)
        rolling_std       = testing_std_as_df.replace(np.nan,testing_std_as_df.ix[window_size - 1]).round(3).iloc[:,0].tolist()

        std = np.std(residual)
        return {'stationary standard_deviation': round(std, 3),
                'anomalies_dict': collections.OrderedDict([(x[index], y_i)
                                                        for index, y_i, avg_i, rs_i in zip(count(), y, avg_list, rolling_std)
                                                        if (y_i > avg_i + (sigma * rs_i)) | (y_i < avg_i - (sigma * rs_i))])}

    # This function is repsonsible for displaying how the function performs on the given dataset.
    @staticmethod
    def plot_results(x, y, window_size, sigma_value=2.0, text_xlabel="X Axis", text_ylabel="Y Axis", applying_rolling_std=False):
        """ Helps in generating the plot and flagging the anamolies.
            Supports both moving and stationary standard deviation. Use the 'applying_rolling_std' to switch
            between the two.
        Args:
        -----
            x (pandas.Series): dependent variable
            y (pandas.Series): independent variable
            window_size (int): rolling window size
            sigma_value (int): value for standard deviation
            text_xlabel (str): label for annotating the X Axis
            text_ylabel (str): label for annotatin the Y Axis
            applying_rolling_std (boolean): True/False for using rolling vs stationary standard deviation
        """
        plt.figure(figsize=(15, 8))
        plt.plot(x, y, "k.")
        y_av = overstay_alert.moving_average(y, window_size)
        
        plt.plot(x, y_av, color='green')
        plt.xlabel(text_xlabel)
        plt.ylabel(text_ylabel)

        # Query for the anomalies and plot the same
        events = {}
        if applying_rolling_std:
            events = overstay_alert.explain_anomalies_rolling_std(x, y, window_size=window_size, sigma=sigma_value)
        else:
            events = overstay_alert.explain_anomalies(x, y, window_size=window_size, sigma=sigma_value)

        # x_anomaly = np.fromiter(events['anomalies_dict'].keys(), dtype=int, count=len(events['anomalies_dict'])) # treats x values as idx WRONG BEHAVIOUR
        x_anomaly = [x for x in events['anomalies_dict'].keys()]
        y_anomaly = np.fromiter(events['anomalies_dict'].values(), dtype=float, count=len(events['anomalies_dict']))
        plt.plot(x_anomaly, y_anomaly, "r*", markersize=12)

        # add grid and lines and enable the plot
        plt.grid(True)
        plt.show()

    @staticmethod
    def get_anomalies(rids, sdt, edt, mm_pure=True, tm_pure=True, window=7, room_sigma=2.0, bath_sigma=2.0, visit_sigma=2.0):
        """ Returns a dict with a constant standard deviation, and anomalies found
        NOTE: YOU SHOULD PUT MAX AND MIN DATETIMES INTO HERE, OR AT LEAST 7 DAYS WORTH OF DATA!!!! 
            - Method is also ment to be run after the day itself. say you want to check 10/10/2018, wait until 11/10/2018 00:00:00, then run with edt = 10/10/2018

            ------- INPUTS:
                    rids (list)    -- list of resident ids
                    sdt (datetime) -- start datetime
                    edt (datetime) -- end datetime
                    mm_pure (bool) -- If true, use only motiion sensors to evaluate time in main room
                    tm_pure (bool) -- If true, use only motion sensors to evaluate time and visits in/to toilet
                    window (int)   -- Size of moving window, default 7
                    sigma (int)    -- Number of standard deviations to consider a point an anomaly, default 2

            
            -------- RETURNS: 
                    Returns a dictionary with key of rid (int) with a value of an OrderedDict with 3 keys: "inRoom", "inBath", "nbath"
                    respectively corresponding to secs_in_room, secs_in_bath, n_visits_bath

                    (dict)          --    {<<rid>>: {"inRoom": <<OrderedDict: k=datetime v=value>>,
                                                     "inBath": <<OrderedDict: k=datetime v=value>>,
                                                     "nBath": <<OrderedDict: k=datetime v=value>>,
                                                    }
                                           }

                                        {'stationary standard_deviation': <<float>>,
                                            'anomalies_dict':  }
        """
        ret_dict = {}

        # Handle "inRoom", "inBath", "nVisitBath"
        # RESULTS >> 'date'  'secs_room'   'secs_bath'    'nvisit_bath'
        results = overstay_alert.test_check_activities_by_date(rids, sdt, edt, mm_pure=mm_pure, tm_pure=tm_pure, print_summary=True)
        shift_logs = shift_log_DAO.get_all_temp_pulse(sdt=sdt, edt=sdt)

        
        for idx,rid in enumerate(rids):
            x_dates  = pd.Series([d['date'] for d in results[idx]])

            y_iroom = pd.Series([d['secs_room'] for d in results[idx]])
            iroom_a = overstay_alert.explain_anomalies_rolling_std(x=x_dates, y=y_iroom, window_size=window, sigma=room_sigma)

            y_ibath = pd.Series([d['secs_bath'] for d in results[idx]])
            ibath_a = overstay_alert.explain_anomalies_rolling_std(x=x_dates, y=y_ibath, window_size=window, sigma=bath_sigma)

            y_nvisit = pd.Series([d['nvisit_bath'] for d in results[idx]])
            nvisit_a = overstay_alert.explain_anomalies_rolling_std(x=x_dates, y=y_nvisit, window_size=window, sigma=visit_sigma)

            # Handle shift form anomalies
            curr_shift_logs = shift_logs[shift_logs['patient_id'] == rid]

            #   TEMPERATURE
            temp_a = [(row.datetime,row.temperature) for idx,row in curr_shift_logs.iterrows() if row.temperature > overstay_alert.temperature_max or row.temperature < overstay_alert.temperature_min]

            #   PULSE RATE
            pulse_a = [(row.datetime,row.pulse_rate) for idx,row in curr_shift_logs.iterrows() if row.pulse_rate > overstay_alert.pulse_pressure_max]

            ret_dict[rid] = {"inRoom": iroom_a['anomalies_dict'],
                             "inBath": ibath_a['anomalies_dict'],
                             "nbath": nvisit_a['anomalies_dict'],
                             "temp": temp_a,
                             "pulse": pulse_a}

        return ret_dict

    # TESTING METHODS ============================================
    @staticmethod
    def test_plot_in_toilet_check(rid, sdt, edt, jump_mins=5):

        tdt = sdt   # Temp datetime
        x_hours  = []
        y_values = []

        counter = 0
        while tdt < edt:
            value = overstay_alert.check_in_toilet(rid=rid, sudo_now=tdt)
            x_hours.append(tdt)
            y_values.append(value)
            tdt += timedelta(minutes=jump_mins)

            if value > 0: print("\t FOUND!! ", tdt, value)
            
            if counter == 0: print(f"sanity check : ", tdt, value)
            counter += 1
            if counter%100 == 0: print(f"sanity check: ", tdt, value)
        
        # Print out specifically points where time > 0
        for i in range(len(x_hours)):
            if y_values[i] > 0:
                print(x_hours[i], y_values[i])
        
        # Plot
        plt.plot(x_hours,y_values)
        plt.gcf().autofmt_xdate()        # beautify the x-labels
        plt.show()

    @staticmethod
    def test_plot_in_room_check(rid, sdt, edt, jump_mins=5):
        tdt = sdt   # Temp datetime
        x_hours  = []
        y_values = []

        counter = 0
        while tdt < edt:
            value = overstay_alert.check_in_room_mdoor(rid=rid, sudo_now=tdt)
            x_hours.append(tdt)
            y_values.append(value)
            tdt += timedelta(minutes=jump_mins)
            
            if counter == 0: print(f"sanity check : ", tdt, value)
            counter += 1
            if counter%10 == 0: print(f"sanity check: ", tdt, value)

        # Plot
        fig,ax1 = plt.subplots()
        plt.plot(x_hours,y_values)
        # beautify the x-labels
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        ax1.xaxis.set_minor_formatter(mdates.DateFormatter("%H-%M:%S"))
        _ = plt.xticks(rotation=45)
        plt.show()
        
    @staticmethod
    def test_check_activities_by_date(rids, sdt, edt, print_summary=False, mm_pure=False, tm_pure=True, plot=False):
        
        results = [] # 'date'  'secs_room'   'secs_bath'    'nvisit_bath'
        times   = []

        for rid in rids:
            start_time = time.clock()
            ret_list = ret_list = overstay_alert.check_activities_by_date(rid=rid, sdt=sdt, edt=edt, mm_pure=mm_pure, tm_pure=tm_pure)
            results.append(ret_list)
            times.append(time.clock() - start_time)

        if print_summary == True:
            summary = []
            for i in range(0, len(rids)):
                n_days = 0
                total_in_room = 0
                total_in_bath = 0
                total_nv_bath = 0

                for d in results[i]:
                    n_days += 1
                    total_in_room += d['secs_room']
                    total_in_bath += d['secs_bath']
                    total_nv_bath += d['nvisit_bath']

                avg_room = total_in_room / n_days
                avg_bath = total_in_bath / n_days
                avg_vist = total_nv_bath / n_days
                summary.append({"rid":rids[i], "avg_room":avg_room, "avg_bath":avg_bath, "avg_visit":avg_vist})

            for r in summary:
                print(f"RID: {r['rid']} \t AVG_ROOM: {format(r['avg_room'], '.2f')} \t AVG_BATH: {format(r['avg_bath'], '.2f')} \t AVG_VIST: {format(r['avg_visit'], '.2f')} \t TIME: {times[i]}")

        elif print_summary == False:
            for i in range(0, len(rids)):
                print(f"========= RID: {rids[i]} ==========")
                for r in results[i]:
                    print(f"\t DATE: {r['date']}, \t ROOM: {r['secs_room']}, \t BATH: {r['secs_bath']}, \t B_VISIT: {r['nvisit_bath']}")
                print(f"===== END TIME: {times[i]} ======")

        return results

    @staticmethod
    def test_anomaly_by_averages(rids, sdt, edt, mm_pure=True, tm_pure=True, print_summary=True, room_sigma=2.0, bath_sigma=2.0, visit_sigma=2.0, window=7, applying_rolling_std=True):

        # RESULTS >> 'date'  'secs_room'   'secs_bath'    'nvisit_bath'
        results = overstay_alert.test_check_activities_by_date(rids, sdt, edt, mm_pure=mm_pure, tm_pure=tm_pure, print_summary=True)
        shift_logs = shift_log_DAO.get_all_temp_pulse(sdt=sdt, edt=edt)

        for idx,rid in enumerate(rids):
            print(f"==================== RID: {rid} ==================================================")
            x_dates  = pd.Series([d['date'] for d in results[idx]])

            y_iroom  = pd.Series([d['secs_room'] for d in results[idx]])
            print("Info of secs room anomalies model:{}".format(overstay_alert.explain_anomalies_rolling_std(x=x_dates, y=y_iroom, window_size=window, sigma=room_sigma)))
            overstay_alert.plot_results(x_dates, y=y_iroom, window_size=window, text_xlabel=f"RID {rid} - Datetime", sigma_value=room_sigma, text_ylabel="secs room", applying_rolling_std=True)

            y_ibath  = pd.Series([d['secs_bath'] for d in results[idx]])
            print("Info of secs bath anomalies model:{}".format(overstay_alert.explain_anomalies_rolling_std(x=x_dates, y=y_ibath, window_size=window, sigma=bath_sigma)))
            overstay_alert.plot_results(x_dates, y=y_ibath, window_size=window, text_xlabel=f"RID {rid} - Datetime", sigma_value=bath_sigma, text_ylabel="secs bath", applying_rolling_std=True)

            y_nvisit = pd.Series([d['nvisit_bath'] for d in results[idx]])
            print("Info of num vbath anomalies model:{}".format(overstay_alert.explain_anomalies_rolling_std(x=x_dates, y=y_nvisit, window_size=window, sigma=visit_sigma)))
            overstay_alert.plot_results(x_dates, y=y_nvisit, window_size=window, text_xlabel=f"RID {rid} - Datetime", sigma_value=visit_sigma, text_ylabel="visits bath", applying_rolling_std=True)

            # Handle shift form anomalies
            curr_shift_logs = shift_logs[shift_logs['patient_id'] == rid]

            #   TEMPERATURE
            temp_a = [(row.datetime,row.temperature) for idx,row in curr_shift_logs.iterrows() if row.temperature > overstay_alert.temperature_max or row.temperature < overstay_alert.temperature_min]

            #   PULSE RATE
            pulse_a = [(row.datetime,row.pulse_rate) for idx,row in curr_shift_logs.iterrows() if row.pulse_rate > overstay_alert.pulse_pressure_max]

            print("ANOMALIES WITH Temperature: ", temp_a)
            print("Anomalies with Pulse Rate:  ", pulse_a)

            print()


# TESTS ======================================================================================
if __name__ == '__main__':

    rdict = {1:"Poh", 3:"Lai" , 5:"Beatrice", 7:"Joy"}

    # rid = 3
    # jump_mins = 5
    # sdt = datetime.datetime.strptime('2018-10-25 18:00:00', '%Y-%m-%d %H:%M:%S')
    # edt = datetime.datetime.strptime('2018-10-26 12:00:00', '%Y-%m-%d %H:%M:%S')
    # overstay_alert.test_plot_in_room_check(rid=rid, sdt=sdt, edt=edt, jump_mins=jump_mins)

    # sdt = datetime.datetime.strptime('2018-09-21 00:00:00', '%Y-%m-%d %H:%M:%S')
    # edt = datetime.datetime.strptime('2018-10-28 00:00:00', '%Y-%m-%d %H:%M:%S')
    # overstay_alert.test_plot_in_toilet_check(rid=rid, sdt=sdt, edt=edt, jump_mins=jump_mins)

    # ============================== TESTING ANOMALY DETECTION WITH PLOT =========================================
    rids = [rid for rid,rname in rdict.items()]
    sdt = datetime.datetime.strptime('2018-08-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    edt = datetime.datetime.strptime('2018-10-30 00:00:00', '%Y-%m-%d %H:%M:%S')
    print("this may take up to 30 secs...")
    overstay_alert.test_anomaly_by_averages(rids, sdt, edt, mm_pure=True, tm_pure=True, print_summary=True, window=7, applying_rolling_std=True)


    # ============================== TESTING ANOMALY DETECTION NO PLOT =========================================
    # rids = [rid for rid,rname in rdict.items()]
    # sdt = datetime.datetime.strptime('2018-08-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    # edt = datetime.datetime.strptime('2018-10-30 00:00:00', '%Y-%m-%d %H:%M:%S')
    # rdict = overstay_alert.get_anomalies(rids, sdt, edt, mm_pure=True, tm_pure=True, window=7, sigma=2)
    # print(rdict)

    

