import datetime, os, sys
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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

    MOTION_TIMEOUT = 5   # mins. motion sensor minutes of inactivity before sending 0 to close off 225 event
    DOOR_CLOSE = 0
    DOOR_OPEN  = 225

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

        if len(last_motions) > 0:      # last motion found
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
        # print("last main door: ", last_mdoor.recieved_timestamp, last_mdoor.event)

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
                # print("\t", logs[0].uuid, [(x.recieved_timestamp, x.event)for x in logs])
                check = overstay_alert.check_isolated_door_motion(last_door=last_mdoor, last_motions=logs, now=now)
                if check > 0: return check

            # Check if any TOILET MOTION
            tmotion_uuid = sdict['tMotion']
            if tmotion_uuid != None:   
                logs =  sensor_log_DAO.get_last_logs(uuid=tmotion_uuid, dt=now, limit=2)  # Get last logs
                # print("\t", logs[0].uuid, [(x.recieved_timestamp, x.event)for x in logs])
                check = overstay_alert.check_isolated_door_motion(last_door=last_mdoor, last_motions=logs, now=now)
                if check > 0: return check

            # Check if any TOILET DOOR  >> any state change
            tdoor_uuid = sdict['tDoor']
            if tdoor_uuid != None:
                logs =  sensor_log_DAO.get_last_logs(uuid=tdoor_uuid, dt=now)                    # Get last log
                # print("\t", logs[0].uuid, [(x.recieved_timestamp, x.event)for x in logs])
                if len(logs) > 0 and logs[0].recieved_timestamp > last_mdoor.recieved_timestamp: # If last log found and after door close
                    # print("\t door: ", tdoor_uuid)
                    return secs_since_last_mdoor

            # Check if any JUVO      >> Get juvo heartrates from last close -- now if any != 0. someone was on the bed
            jtarget = sdict['juvo']
            if jtarget != None:
                vitals_json = JuvoAPI.get_target_vitals(target=jtarget, start_time=last_mdoor.recieved_timestamp, end_time=now)
                # print("Getting vitals from last_mdoor: ", last_mdoor.recieved_timestamp, now)
                heart_pd,_  = JuvoAPI.extract_heart_breath_from_vitals(json=vitals_json)
                if len(heart_pd.index) > 0:
                    # print("\t found heart rates: ", heart_pd)
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

                # # Check 2.3 >> both events open NOTE: WITH THIS SITUATION WE cannot be certain where person is. real ghetto
                # if t_mlogs[0].event == 0 and m_mlogs[0].event == 0:
                #     if t_mlogs[0].recieved_timestamp > m_mlogs[0].recieved_timestamp:
                #         return (now - t_mlogs[0].recieved_timestamp).total_seconds()

        return 0


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
        


# TESTS ======================================================================================
if __name__ == '__main__':
    rid = 3
    jump_mins = 5
    sdt = datetime.datetime.strptime('2018-10-25 18:00:00', '%Y-%m-%d %H:%M:%S')
    edt = datetime.datetime.strptime('2018-10-26 12:00:00', '%Y-%m-%d %H:%M:%S')
    # overstay_alert.test_plot_in_room_check(rid=rid, sdt=sdt, edt=edt, jump_mins=jump_mins)

    sdt = datetime.datetime.strptime('2018-09-21 00:00:00', '%Y-%m-%d %H:%M:%S')
    edt = datetime.datetime.strptime('2018-10-28 00:00:00', '%Y-%m-%d %H:%M:%S')

    sdt = datetime.datetime.strptime('2018-09-24 18:35:00', '%Y-%m-%d %H:%M:%S')
    edt = datetime.datetime.strptime('2018-09-24 19:40:00', '%Y-%m-%d %H:%M:%S')
    overstay_alert.test_plot_in_toilet_check(rid=rid, sdt=sdt, edt=edt, jump_mins=jump_mins)
    

