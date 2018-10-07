import datetime, os, sys, math
from datetime import timedelta

if __name__ == '__main__':  sys.path.append("..")
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

class Sensor_mgmt(object):

    # RETURN STATUS CODES
    INVALID_SENSOR = -1
    OK             = 0     # Can be OK and LOW_BATT at the same time
    DISCONNECTED   = 1
    LOW_BATT       = 2
    CHECK_WARN     = 3    # Potentially down

    # SETTINGS
    batt_thresh  = 10    # In percent


    @classmethod
    def get_sensor_status(cls, uuid, retBatteryLevel=False):
        '''
        Returns 'up' | 'down' status of sensors.
        For new sensors, Im assuming that at least a single record is sent and thus will trigger true.

        Inputs:
        uuid (str)
        retBatteryLevel (boolean)

        Return:
        1. A List of status codes: See class variables
        2. A list of Battery level
            - None if Juvo
            - Empty if no records found. e.g. Door sensors only send battery level logs when on low battery
            - Single value in %
        i.e. ([1,3], [75])
        i.e. ([1]  , [])        // Battery or newly installed sensor
        i.e. ([0]  , [None]])   // Juvo
        '''
        # AREAS OF IMPROVEMENT
        # 1. Juvo Bed sensor: Warning triggered if no sleep in the past sleep period 9pm-9am. What about if sleep = 1sec? May also be a problem with elderly
        #   - Maybe look at the breakdown period would be better >> light, deep, awake that kind of thing
        # 2. What if sensor partially breaks, sysmon sends, but no sensor logs? Dont think this can be detected also
        ret_codes = []
        batt_lvl  = None

        curr_time = datetime.datetime.now()
        curr_time_m1d = curr_time - datetime.timedelta(days=1)

        try: sensor = sensor_DAO.get_sensors(uuid=uuid)[0]
        except IndexError:
            ret_codes.append(cls.INVALID_SENSOR)
            return ret_codes
        uuid = sensor.uuid
        type = sensor.type

        isDoor   = True if type == "door" else False
        isMotion = True if type == "motion" else False
        isBed    = True if type == "bed sensor" else False

        #LEGACY -- "disconnected" only exists in master students' data set. As this was thrown by gateway
        last_sysmons = sysmon_log_DAO.get_last_sysmon(uuid)
        if len(last_sysmons) > 0:
            if last_sysmons[0].key == "disconnected": ret_codes.append(cls.DISCONNECTED)

        if isDoor:    # DOOR SENSOR
            # Check1: sensor update within 24 hours
            # we are assuming that the door closes at least once a day
            past24hrs_data = sensor_log_DAO.get_logs(uuid=uuid,  start_datetime=curr_time_m1d, end_datetime=curr_time)
            if len(past24hrs_data) > 0: ret_codes.append(cls.CHECK_WARN)
            else: ret_codes.append(cls.OK)


        elif isMotion:  # MOTION SENSOR
            last_batt = sysmon_log_DAO.get_last_battery_level(uuid=uuid)
            if last_batt != None:
                batt_update_period = (curr_time - last_batt.recieved_timestamp).total_seconds()

                # Check 1: hourly battery update. aeotec multisensor 6 should send battery level sysmon updates on the hour
                # This may just be Boon Thais' configs
                if batt_update_period > (60 * 60 * 1.2): ret_codes.append(cls.CHECK_WARN)
                else: ret_codes.append(cls.OK)


        elif isBed:     # BED SENSOR (JUVO)
            juvo = JuvoAPI()
            # Check 1: Sleep logged within past sleep period 9pm - 9am
            day_timebreak   = curr_time.replace(hour=9, minute=0, second=0, microsecond=0)
            night_timebreak = curr_time.replace(hour=21, minute=0, second=0, microsecond=0)
            if curr_time >  day_timebreak and curr_time < night_timebreak:    # If current time is between 9am and 9pm
                sleeps = juvo.get_total_sleep_by_day(target=sensor.juvo_target, start_date=curr_time_m1d, end_date=curr_time_m1d)
                if len(sleeps) > 0: ret_codes.append(cls.OK)    # sleep recorded
                else: ret_codes.append(cls.CHECK_WARN)          # no sleep recorded

        else:
           ret_codes.append(cls.INVALID_SENSOR)

        # Check2: Battery level
        if isMotion or isDoor:
            last_batt = sysmon_log_DAO.get_last_battery_level(uuid=uuid)
            if last_batt != None:       # Sysmon batt event found
                batt_lvl = last_batt.event
                if batt_lvl < cls.batt_thresh:
                    ret_codes.append(cls.LOW_BATT)
            else:                       # No Sysmon batt event found, door sensor high batt, or newly installed sensor
                batt_lvl = []

        # Return Values
        if retBatteryLevel: return ret_codes, batt_lvl
        else: return ret_codes

    @classmethod
    def get_all_sensor_status(cls, retBatteryLevel=False):
        '''
        Returns 'up' | 'down' status of ALL sensors.

        Inputs:
        retBatteryLevel -- True, return battery level if exists. Default false

        Return:
            list of sensors, status codes, and optionally battery levels:
            NOTE: Battery level can be 'None' if no records are found

            [ [Sensor.Entity, [Status, Codes, battLVL]],
              [Sensor.Entity, [Status, Codes, None]]...
            ]

            See list of status codes
        '''
        # Ret list in form: [[uuid, [status codes], [uuid, [status codes]]]]
        sensor_status = []

        # List of all Sensors
        sensors = sensor_DAO.get_sensors()

        # Iterate all sensors and get statuss
        for sensor in sensors:
            uuid   = sensor.uuid
            print(uuid)
            status = cls.get_sensor_status(uuid=uuid, retBatteryLevel=retBatteryLevel)
            if retBatteryLevel: sensor_status.append([uuid, status[0], status[1]])
            else: sensor_status.append([uuid, status])

        return sensor_status


    @classmethod
    def get_down_periods_motion(cls, uuid, start_dt, end_dt):
        '''
        Checks if readings during `start_dt` to `end_dt` can be trusted. i.e.
        If we can confirm sensor is ON during the period

        INPUTS
        uuid (str)
        start_dt (datetime)
        end_dt (datetime)

        RETURNS:
        list of periods where sensor CANNOT be trusted: [(start_dt, end_dt), ...]
        if empty, period can be trusted
        '''
        # Expand period by 2 hours, 1 before start_dt and 1 hour after end_dt
        # This is to gather the sysmon battery updates
        start_dt_buff = start_dt - timedelta(hours=1.2)
        end_dt_buff   = end_dt   + timedelta(hours=1.2)

        # get all sysmon battery readings within start_dt and end_dt
        records = sysmon_log_DAO.get_logs(uuid=uuid, key=Sysmon_Log.key_battery, start_dt=start_dt_buff, end_dt=end_dt_buff, descDT=False, limit=0)
        # CHECK 1: If no records found, sensor is confirmed down during the period, but just
        if records == None: return [(start_dt, end_dt)]

        # CHECK 2: sysmon battery updates >> hourly sysmon battery updates are ASSURED
        down_periods = []

        #   >> Corner case, when period given is current. and only 1 batt sysmon can be found before
        #   >> Return true if diff has been less than 1 hour. Assume still up
        if len(records) == 1:
            curr_ts = records[0][Sysmon_Log.recieved_timestamp_tname]
            if curr_ts < start_dt and (start_dt-curr_ts) < timedelta(hours=1.2): return []

        prev_ts      = None
        for i in range(0, len(records)):     # Greedy

            # Initial assignment
            curr_ts = records[i][Sysmon_Log.recieved_timestamp_tname]
            if prev_ts == None:
                prev_ts = curr_ts
                continue

            # Nothing wrong >> update was within 1 hour + buffer
            if (curr_ts - prev_ts) / timedelta(minutes=1) <= (60 * 1.2):
                prev_ts = curr_ts
                continue

            # Something wrong >> update was > 1 hour + buffer. There is a missing battery update
            pred_missing = prev_ts + timedelta(hours=1)

            #       >> Assumption here is that there will never be a period where sensor revives and sends a reading without a sysmon battery update
            #           >> Therefore if sensor is brought back up, it sends a sysmon battery update soon after
            enc_logs     = Sensor_mgmt.get_enclosing_logs(start_dt=prev_ts, end_dt=curr_ts, target_dt=pred_missing)
            # ^ last before and first atfer reading (sensor and sysmon) from where the next missing battery update is

            if len(enc_logs) == 0: down_periods.append([prev_ts, curr_ts])
            if len(enc_logs) == 2: down_periods.append([enc_logs[0], enc_logs[1]])
            if len(enc_logs) == 1:
                if enc_logs[0] < pred_missing: down_periods.append([enc_logs[0], curr_ts])
                if enc_logs[0] > pred_missing: down_periods.append([prev_ts, enc_logs[0]])

            # shift down 1
            prev_ts = curr_ts

        return down_periods


    @classmethod
    def get_enclosing_logs(cls, start_dt, end_dt, target_dt):
        '''
        Given a target datetime, returns...
        Last record (sysmon or sensor reading) before the target and first record after the target

        Inputs:
        start_dt (datetime)
        end_dt (datetime)
        target_dt (datetime)

        Returns:
        [before_dt, after_dt]
        NOTE: dts can be None, meaning no records during that period
        '''
        enc_sensor = sensor_log_DAO.get_enclosing_logs(start_dt=start_dt, end_dt=end_dt, target_dt=target_dt)     # Sensor readings: 1st before target, 1st after target
        enc_sysmon = sysmon_log_DAO.get_enclosing_logs(start_dt=start_dt, end_dt=end_dt, target_dt=target_dt)     # Sysmon readings: 1st before target, 1st after target

        enc_logs = [None, None]
        if   enc_sensor[0] == None and enc_sysmon[0] != None: enc_logs[0] = enc_sysmon[0]
        elif enc_sensor[0] != None and enc_sysmon[0] == None: enc_logs[0] = enc_sensor[0]
        elif enc_sensor[0] < enc_sysmon[0]: enc_logs[0] = enc_sysmon[0]
        else: enc_logs[0] = enc_sensor[0]

        if   enc_sensor[1] == None and enc_sysmon[1] != None: enc_logs[1] = enc_sysmon[1]
        elif enc_sensor[1] != None and enc_sysmon[1] == None: enc_logs[1] = enc_sensor[1]
        elif enc_sensor[1] < enc_sysmon[1]: enc_logs[1] = enc_sensor[1]
        else: enc_logs[1] = enc_sysmon[1]

        return enc_logs


    @classmethod
    def get_down_periods_Juvo(cls, target, start_dt, end_dt):
        '''
        Returns the down period for Juvo Bed sensors
        Logic is based on the Environment readings, which should be read in continous 5 minute windows

        Inputs:
        target   (int)
        start_dt (datetime)
        end_dt   (datetime)

        Returns:
        list -- [[start,end], ...]
        '''

        readings = JuvoAPI.get_target_environ_stats(target=target, start_time=start_dt, end_time=end_dt)

        # No readings, therefore all down
        if readings == None: return [[start_dt, end_dt]]

        readings.sort(key=lambda x: x['local_start_time'], reverse=False) # Sorted in increasing time order

        down_periods = []
        prev_sdt = None
        prev_edt = None
        for reading in readings:
            curr_sdt = reading['local_start_time']
            curr_edt = reading['local_end_time']

            # Inital assignment
            if prev_sdt==None and prev_edt==None: prev_sdt, prev_edt = curr_sdt, curr_edt

            # Periods not continuous
            elif prev_edt != start_dt:
                down_periods.append([prev_edt, curr_sdt])
                prev_sdt = curr_sdt
                prev_edt = curr_edt

        # What about no readings at all
        return down_periods


    # @classmethod
    # def get_down_periods_door(cls, uuid, start_dt, end_dt):
    #     '''
    #     Returns the down periods for the door sensor
    #     NOTE: down/up can only be assigned to a daily/24 hour basis, hard to get more accurate than that

    #     Inputs:
    #     uuid     (str)
    #     start_dt (datetime) -- Inclusive
    #     end_dt   (datetime) -- Inclusive

    #     Return
    #     List of down time: [[start,end]...]
    #     '''

    #     # Split into periods whereby the 10th would refer to 12pm 9th, to 12pm 10th
    #     start_date = start_dt.replace(hours=0, minutes=0, seconds=0)
    #     end_date   = end_dt.replace(hours=0, minutes=0, seconds=0)
    #     date_diff  = math.floor((end_date - start_date) / timedelta(days=1))

    #     # Get all sensor of this uuid between start and end dates
    #     logs = sensor_log_DAO.get_logs(uuid=uuid, start_datetime=start_date, end_datetime=end_date).sort(key = lambda x: x.recieved_timestamp) # ASC

    #     # C1: if any readings within the date, consider up
    #     status = []
    #     for i in range(0, date_diff):
    #         curr_date = (start_date + timedelta(days=1)).replace(hour=12)
    #         curr_start = (curr_date - timedelta(days=1)).replace(hour=12)
    #         curr_end   = curr_date

    #         # if any readings consider the date up
    #         filtered_logs = [x for x in logs if x.recieved_timestamp >= curr_start and x.recieved_timestamp <= curr_end]


    #         if len(filtered_logs) > 0:      # Logs found, consider up
    #             status.append(True)
    #             continue

    #         else:                           # No logs, finetune
    #             # Get owner by period
    #             # Get Juvo owner by period

    #             # Use Juvo to finetune


    Juvo_SLEEP = 1      # Someone was sleeping
    JUVO_NOONE = 0      # No one slept
    JUVO_DOWN  = -1     # There is no way to know if anyone slept or not, so just scrumb the entire preiod as down
    @classmethod
    def check_sleep_noone_down_juvo(cls, target, date):
        '''
        Utility method to investigate the reason for a missing date (i.e. no sleep_summary readings from sensor)
        NOTE: Will return weird results if given a date that has readings

        Inputs:
        target (int)
        date (datetime) -- Sleep period for 12th considers 12th noon - 13th noon

        Returns:
        JUVO_NOONE = 0      -- Probably no one slept that night
        JUVO_DOWN  = 1      -- Sensor is down during that date
        '''

        # Juvo looks at night after, but we want to look at the night before
        prev_date = date - timedelta(days=1) # 12 am   of 1 day before date
        end_dt   = date.replace(hour=12)     # 12 noon of date
        start_dt = end_dt - timedelta(days=1)   # 12 noon of 1 day before date

        sleep_summaries = JuvoAPI.get_target_sleep_summaries(target=target, start_date=prev_date, end_date=prev_date)
        down_periods = cls.get_down_periods_Juvo(target=target, start_dt=start_dt, end_dt=end_dt)

        if sleep_summaries != None: return cls.Juvo_SLEEP       # C1: If sleep summaries found, then JUVO_SLEEP
        elif len(down_periods) == 0: return cls.JUVO_NOONE      # C2: If no sleep summaries found, AND  0 down periods, then JUVO_NOONE
        else: return cls.JUVO_DOWN                              # C3: If no sleep summaries found, AND any down period: JUVO DOWN



# TESTS ======================================================================================
if __name__ == '__main__':

    # # Room 1
    # print("================ ROOM 1 ================")
    # uuid = "2005-m-01"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # uuid = "2005-m-02"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # uuid = "2005-d-01"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # uuid = "2005-d-02"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # uuid = "2005-j-01"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # # Room 2
    # print("================ ROOM 1 ================")
    # uuid = "2006-m-01"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # uuid = "2006-m-02"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # uuid = "2006-d-01"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # uuid = "2006-d-02"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # uuid = "2006-j-01"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # # Room 3
    # print("================ ROOM 3 ================")
    # uuid = "2100-room 3-m-01"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # uuid = "2100-room 3-m-02"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # uuid = "2100-room 3-d-01"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # uuid = "2100-room 3-j-01"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # # Room 4
    # print("================ ROOM 4 ================")
    # uuid = "2100-room 4-m-01"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # uuid = "2100-room 4-m-02"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # uuid = "2100-room 4-d-01"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # # ADAM
    # print("================ ADAM ROAD ================")
    # uuid = "2100-room 4-m-01"
    # print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    # All
    # print("=============== ALL SENSORS ==============")
    # for ss in Sensor_mgmt.get_all_sensor_status(retBatteryLevel=True):
    #     print(ss)

    # for ss in Sensor_mgmt.get_all_sensor_status(retBatteryLevel=False):
    #     print(ss)
    uuid = "2005-m-02"
    sdt = datetime.datetime(year=2018, month=3, day=2, minute=15, second=46)
    sdt2 = datetime.datetime(year=2018, month=3, day=2)
    edt = datetime.datetime(year=2018, month=10, day=4, hour=22, minute=20, second=40)
    down_periods = Sensor_mgmt.get_down_periods_motion(uuid=uuid, start_dt=sdt2, end_dt=edt)
    down_periods = Sensor_mgmt.get_down_periods_motion(uuid=uuid, start_dt=sdt, end_dt=edt)
    for p in down_periods: print(p)
