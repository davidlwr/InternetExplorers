import datetime, os, sys, time
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from itertools import islice
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

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

class overstay_alert(object):

    MOTION_TIMEOUT = 4   # mins. motion sensor minutes of inactivity before sending 0 to close off 225 event
    DOOR_CLOSE = 0
    DOOR_OPEN  = 255

    MOTION_START = 255
    MOTION_END   = 0

    # RETURN CODES:
    NO_MAIN_DOOR = -1    # Unable to run algo, as no main door sensor found
    DC_MAIN_DOOR = -2    # Unable to run algo, main doow is down. NOTE: no real action needed, CHECKWARN should already be sent
    INVALID_SSET = -3    # Unable to run algo, due to lack of combination of sensors
    
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


    @staticmethod
    def check_activities_by_date(rid, sdt, edt):
        '''
        Returns time spent in toilet by date. both sdt and edt are inclusive
        NOTE: This is a greedy algo, sort of ghetto, theres better logic, but I dont have time left to do them.

        rid (int)      -- resident id
        sdt (datetime) -- start datetime
        edt (datetime) -- end datetime
        '''
        # DEAL WITH TOILET DOOR AS WELL
        # List of currently owned sensors      
        sensors = sensor_DAO.get_owned_sensors(rid=rid, dt=edt)
        sdict = overstay_alert.extract_sensors(sensors=sensors)
        uuids = [uuid for k,uuid in sdict.items() if uuid != None]

        # Get all sensor logs
        logs_dt = sensor_log_DAO.get_all_logs()

        curr_sdt = sdt.replace(hour=0, second=0, minute=0, microsecond=0)
        edate    = edt.replace(hour=0, second=0, minute=0, microsecond=0)

        # Loop between dates and get summary statistics
        ret_list = []
        while curr_sdt <= edate:
            curr_edt = curr_sdt.replace(hour=23, minute=59, second=59)
            
            # Pull out all logs within the current date
            curr_logs = logs_dt[(logs_dt['recieved_timestamp'] >= curr_sdt) & (logs_dt['recieved_timestamp'] <= curr_edt)]
            curr_logs = curr_logs[curr_logs['uuid'].isin(uuids)]
            curr_logs.sort_values(by='recieved_timestamp', ascending=True, inplace=True)
            
            # Summary values
            time_in_room = 0
            time_in_bath = 0
            nvisits_bath = 0

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
                            time_in_room += (row.recieved_timestamp - curr_sdt).total_seconds()

                    # If current door event is OPEN and previous door event is CLOSE
                    elif (row.event == overstay_alert.DOOR_OPEN and prev_md.event == overstay_alert.DOOR_CLOSE):
                        # Check if any motion in room while door was closed. If yes, then take this as in room
                            if type(prev_tm) != type(None): 
                                if prev_tm.recieved_timestamp > prev_md.recieved_timestamp: 
                                    time_in_room += (row.recieved_timestamp - prev_md.recieved_timestamp).total_seconds()

                            elif type(prev_mm) != type(None): 
                                if prev_mm.recieved_timestamp > prev_md.recieved_timestamp:
                                    time_in_room += (row.recieved_timestamp - prev_md.recieved_timestamp).total_seconds()

                    prev_md = row

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

                # If main Motion
                if row.uuid == sdict["mMotion"]: prev_mm = row
                
            # Deal with trailing status
            #   Final main door == closed
            if type(prev_md) != type(None):
                if prev_md.event == overstay_alert.DOOR_CLOSE:
                    if type(prev_tm) != type(None):     # Check for any motion inside toilet motion
                        if prev_tm.recieved_timestamp > prev_md.recieved_timestamp:  
                            time_in_room += (curr_edt - prev_md.recieved_timestamp).total_seconds()

                    elif type(prev_mm) != type(None):   # Check for any motion inside main motion
                        if prev_mm.recieved_timestamp > prev_md.recieved_timestamp:  
                            time_in_room += (curr_edt - prev_md.recieved_timestamp).total_seconds()

            #   Final toilet motion open
            if type(prev_tm) != type(None):
                if prev_tm.event == overstay_alert.MOTION_START:
                    time_in_bath += (curr_edt - prev_tm.recieved_timestamp).total_seconds()

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
                        time_in_room += (row.recieved_timestamp - curr_sdt).total_seconds()

                # If current door event is OPEN and previous door event is CLOSE
                elif (row.event == overstay_alert.DOOR_OPEN and prev_md.event == overstay_alert.DOOR_CLOSE):
                    # Check if any motion in room while door was closed. If yes, then take this as in room
                        if type(prev_tm) != type(None): 
                            if prev_tm.recieved_timestamp > prev_md.recieved_timestamp: 
                                time_in_room += (row.recieved_timestamp - prev_md.recieved_timestamp).total_seconds()

                        elif type(prev_mm) != type(None): 
                            if prev_mm.recieved_timestamp > prev_md.recieved_timestamp:
                                time_in_room += (row.recieved_timestamp - prev_md.recieved_timestamp).total_seconds()

                prev_md = row

            # If toilet Motion                
            if row.uuid == sdict["tMotion"]: prev_tm = row
            # If main Motion
            if row.uuid == sdict["mMotion"]: prev_mm = row
            
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
        while i < len(curr_logs):
            row = curr_logs.iloc[i]

            # ALSO POTENTIALY BUGGY, but not by alot. since data suggest residents dont really sleep for a long period of time. More like they nap alot
            if first_motion_found == False and row.recieved_timestamp < curr_sdt.replace(hour=6) and (row.uuid == sdict['mMotion'] or row.uuid == sdict['mMotion']):
                time_in_room += (row.recieved_timestamp - curr_sdt).total_seconds() 
                first_motion_found == True

            elif row.uuid == sdict['mMotion'] or row.uuid == sdict['mMotion']:
                uuid_searching_end = row.uuid

                # Look forward
                for j in range(i, len(curr_logs)):
                    future_row = curr_logs.iloc[j]

                    if future_row.uuid == uuid_searching_end and future_row.event == overstay_alert.MOTION_END:
                        time_in_room += (future_row.recieved_timestamp - row.recieved_timestamp - timedelta(minutes=overstay_alert.MOTION_TIMEOUT)).total_seconds()

                        # Skip i ahead to after j
                        uuid_searcing_end = None    # Set to None when search ends
                        i += j - i 

                    # If another motion sensor starts within the room, look for its end instead
                    elif (future_row.uuid  == sdict['mMotion'] or future_row.uuid == sdict['mMotion']) and future_row.event == overstay_alert.MOTION.START:
                        uuid_searching_end = future_row.uuid

                    # Tail end, open seach, but we hit edt >> POTENTIALLY BUGGY AF
                    elif j == len(curr_logs) - 1: 
                        time_in_room += (curr_edt - row.recieved_timestamp).total_seconds()

            # Increment counter
            i += 1
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
                        if prev_tm.event == overstay_alert.MOTION_END and prev_tm.recieved_timestamp > (prev_td.recieved_timestamp + timedelta(minutes=overstay_alerts.MOTION_TIMEOUT)):  
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
    def test_check_activities_by_date(rids, sdt, edt, print_summary=False):
        
        results = []
        times = []

        for rid in rids:
            start_time = time.clock()
            ret_list = overstay_alert.check_activities_by_date(rid=rid, sdt=sdt, edt=edt)
            results.append(ret_list)
            times.append(time.clock() - start_time)


        if print_summary:
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
                print(f"RID: {r['rid']} \t AVG_ROOM: {format(r['avg_room'], '.2f')} \t AVG_BATH: {format(r['avg_bath'], '.2f')} \t AVG_VIST: {format(r['avg_visit'], '.2f')}, TIME: {times[i]}")

        else:
            for i in range(0, len(rids)):
                print(f"========= RID: {rids[i]} ==========")
                for r in results[i]:
                    print(f"\t DATE: {r['date']}, \t ROOM: {r['secs_room']}, \t BATH: {r['secs_bath']}, \t B_VISIT: {r['nvisit_bath']}")
                print(f"===== END TIME: {times[i]} ======")



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


    rids = [rid for rid,rname in rdict.items()]
    rids = [5]
    sdt = datetime.datetime.strptime('2018-10-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    edt = datetime.datetime.strptime('2018-10-30 00:00:00', '%Y-%m-%d %H:%M:%S')
    overstay_alert.test_check_in_toilet_by_date(rids, sdt, edt, print_summary=False)

    

