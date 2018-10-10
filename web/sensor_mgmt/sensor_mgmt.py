import datetime, os, sys, math, time
from datetime import timedelta
from dateutil import parser

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
    batt_thresh  = 10     # percent
    motion_thresh = 1.2   # hours
    juvo_thresh  = 50     # minutes >> Environment Stats >> Difference between reading and API availability


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
            status = cls.get_sensor_status(uuid=uuid, retBatteryLevel=retBatteryLevel)
            if retBatteryLevel: sensor_status.append([uuid, status[0], status[1]])
            else: sensor_status.append([uuid, status])

        return sensor_status


    @classmethod
    def get_sensor_status_v2(cls, uuid, retBatteryLevel=False):
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
            return cls.get_curr_status_door(uuid=uuid, retBatteryLevel=retBatteryLevel)

        elif isMotion:  # MOTION SENSOR
            return cls.get_curr_status_motion(uuid=uuid, retBatteryLevel=retBatteryLevel)

        elif isBed:     # BED SENSOR (JUVO)
            return cls.get_curr_status_juvo(target=sensor.juvo_target)

        else:
           ret_codes.append(cls.INVALID_SENSOR)
           return ret_codes


    @classmethod
    def get_all_sensor_status_v2(cls, retBatteryLevel=False):
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
            status = cls.get_sensor_status_v2(uuid=uuid, retBatteryLevel=retBatteryLevel)
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
        if len(records) == 0: return [(start_dt, end_dt)]

        # CHECK 2: sysmon battery updates >> hourly sysmon battery updates are ASSURED
        down_periods = []

        #   >> Corner case, when period given is current. and only 1 batt sysmon can be found before
        #   >> Return true if diff has been less than 1 hour. Assume still up
        if len(records) == 1:
            curr_ts = records[0][Sysmon_Log.recieved_timestamp_tname]
            if curr_ts < start_dt and (start_dt-curr_ts) < timedelta(hours=cls.motion_thresh): return []

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
    def get_curr_status_motion(cls, uuid, retBatteryLevel=False):
        '''
        Returns list of status codes. See class vars

        Inputs:
        uuid (str)
        '''
        # Get down periods
        now = datetime.datetime.now()
        down_periods = cls.get_down_periods_motion(uuid=uuid, start_dt=now, end_dt=now)
        ret_codes = []
        down = False
        for p in down_periods:          # Check if current time is within a down period
            # print(p)
            if p[0] <= now and now <= p[1]: 
                down = True
                break
        ret_codes.append(cls.CHECK_WARN if down else cls.OK)

        # Battery level?
        if retBatteryLevel == False: return ret_codes
        else:
            batt_lvl = []
            last_batt = sysmon_log_DAO.get_last_battery_level(uuid=uuid)
            if last_batt != None:       # Sysmon batt event found
                batt_lvl.append(last_batt.event)
                if last_batt.event < cls.batt_thresh:
                    ret_codes.append(cls.LOW_BATT)
            return ret_codes, batt_lvl


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

        logs = readings['data']['stats']
        logs.sort(key=lambda x:  parser.parse(x['local_start_time'])) # Sorted in increasing time order

        down_periods = []
        prev_sdt = None
        prev_edt = None
        for log in logs:
            curr_sdt = parser.parse(log['local_start_time']).replace(tzinfo=None)
            curr_edt = parser.parse(log['local_end_time']).replace(tzinfo=None)

            # Inital assignment
            if prev_sdt==None and prev_edt==None:
                prev_sdt = curr_sdt
                prev_edt = curr_edt
                continue

            # Periods not continuous
            if (curr_sdt - prev_edt) > timedelta(minutes=10):
                down_periods.append([prev_edt, curr_sdt])

            prev_sdt = curr_sdt
            prev_edt = curr_edt

        # Deal with last log - curr time
        # Find the previous 5 divisible minute (when environ stats should have sent data)
        edt = datetime.datetime.now()
        edt = edt.replace(minute=(math.floor(edt.minute / 5) * 5), second=0, microsecond=0)
        cutoff = edt - timedelta(minutes=cls.juvo_thresh)           # lag between data reading and availablity on API
        if cutoff - prev_edt > timedelta(minutes=cls.juvo_thresh):  # Difference > Lag thresh. Therefore is down not lagged
            down_periods.append([prev_edt, cutoff])

        return down_periods


    @classmethod
    def get_curr_status_juvo(cls, target):
        '''
        Returns status of Juvo Bed sensor based on last received environment statistic
        if last received was > threshold mins, then return down.

        target (int) 
        '''
        # Get all environ readings for past 1 hour
        end_dt   = datetime.datetime.now()      # Also the current time
        start_dt = end_dt - timedelta(hours=1)
        readings = JuvoAPI.get_target_environ_stats(target=target, start_time=start_dt, end_time=end_dt)

        ret_codes = []
        if readings == None: ret_codes.append(cls.CHECK_WARN)        # No readings, therefore down
        elif len(readings['data']['stats']) == 0: ret_codes.append(cls.CHECK_WARN)
        else:   
            # Compare last reading with current time, against threshold
            logs = readings['data']['stats']
            if(len(logs) > 0):
                logs.sort(key=lambda x:  parser.parse(x['local_start_time'])) # Sorted in increasing time order
                last_log = logs[-1]
                last_log_edt = parser.parse(last_log['local_end_time']).replace(tzinfo=None)

                time_since_update = end_dt - last_log_edt
                if time_since_update > timedelta(minutes=cls.juvo_thresh): ret_codes.append(cls.CHECK_WARN)
                else: ret_codes.append(cls.OK)
            else:
                ret_codes.append(cls.CHECK_WARN)

        return ret_codes, []

    @classmethod
    def get_down_periods_door(cls, uuid, start_dt, end_dt):
        '''
        Returns the down periods for the door sensor
        NOTE: down/up can only be assigned to a daily/24 hour basis, hard to get more accurate than that

        Inputs:
        uuid     (str)
        start_dt (datetime) -- Inclusive
        end_dt   (datetime) -- Inclusive

        Return
        List of down time: [[start,end]...]
        '''

        # Split into periods whereby the 10th would refer to 12pm 9th, to 12pm 10th
        start_date = start_dt.replace(hour=0, minute=0, second=0) - timedelta(days=1) # Expand by 1 day, in case start and end are the same day
        end_date   = end_dt.replace(hour=0, minute=0, second=0)  

        # Get all sensor logs of this uuid between start and end dates
        logs = sensor_log_DAO.get_logs(uuid=uuid, start_datetime=start_date, end_datetime=end_date)
        logs.sort(key = lambda x: x.recieved_timestamp) # ASC

        # Treat bathroom and main door differently
        location = sensor_DAO.get_sensors(uuid=uuid)[0].location
        if location == "toilet":
            if logs == None or len(logs) == 0: # No readings since, send warning
                return [[start_date.replace(hour=0, minute=0), end_date.replace(hour=23, minute=59)]]
            else: return []

        # if no records, consider down
        if len(logs) == 0:
            missing_dates = [start_date]
        else:
            # Find dates without logs
            logs_d_only = [l.recieved_timestamp.replace(hour=0, minute=0, microsecond=0) for l in logs]
            min_log_dt = logs_d_only[0]
            max_log_dt = logs_d_only[-1]
            full_cal = set(min_log_dt + timedelta(x) for x in range((max_log_dt - min_log_dt).days))    # All dates between start and end
            missing_dates = sorted(full_cal - set(logs_d_only))

            # Slice out dates with no owner
            ownership = sensor_DAO.get_ownership_hist(uuid=uuid, start_dt=start_dt, end_dt=end_dt)
            min_dt = max_dt = datetime.datetime.now()
            for p in ownership[uuid]:
                if p[1] != None and (p[1] < min_dt): min_dt = p[1].replace(hour=0, minute=0, microsecond=0)
                if p[2] != None and (p[2] > max_dt): max_dt = p[2].replace(hour=0, minute=0, microsecond=0)

            ownerless = []
            if min_dt > start_dt: ownerless += [start_dt + timedelta(x) for x in range((min_dt - start_dt).days)]
            if max_dt < end_dt:   ownerless += [max_dt + timedelta(x) for x in range((end_dt - max_dt).days)]
            missing_dates = sorted(set(missing_dates) - set(ownerless))

        # Fine tune periods without logs, it may just be the case where no one uses the door at all
        # Assumption: reisdents sleep with doors closed. Therefore use Juvo to fine-tune
        down_periods = []
        for missing in missing_dates:
            missing_end   = missing.replace(hour=12)
            missing_start = missing_end - timedelta(days=1)

            # Get owner by period
            door_ownership = sensor_DAO.get_ownership_hist(uuid=uuid, start_dt=missing_start, end_dt=missing_end)
            rid_owners = [v[0][0] for k,v in door_ownership.items()]

            # Get Juvo owner by period ERROR HERE MAKE NEW QUERY
            juvo_ownership = sensor_DAO.get_ownership_hist(start_dt=missing_start, end_dt=missing_end, type="bed sensor")
            juvo_uuid = None
            for k,v in juvo_ownership.items():
                if v[0][0] in rid_owners:
                    juvo_uuid = k
                    break

            if juvo_uuid == None: # This resident didnt own a bed sensor this day
                down_periods.append([missing.replace(hour=0, minute=0), missing.replace(hour=23, minute=59)])  

            if juvo_uuid != None:   # Attempt to find if owner slept this period
                target = None
                for s in sensor_DAO.get_sensors(uuid=juvo_uuid):
                    target = s.juvo_target
                    break

                if target == None:  # This resident didnt own a bed sensor this day
                    down_periods.append([missing.replace(hour=0, minute=0), missing.replace(hour=23, minute=59)])     

                # Check if sleep was detected
                juvo_offset_dt = missing - timedelta(days=1)    # i.e. Sleep for 10th = 10th 12pm to 11th 12pm
                records = JuvoAPI.get_target_sleep_summaries(target, juvo_offset_dt, juvo_offset_dt)['sleep_summaries']
                for r in records:
                    total_sleep = r['light'] + r['deep'] + r['awake']
                    if total_sleep < 0:     # Sleep detected, no door detected. assume door is down
                        down_periods.append([missing.replace(hour=0, minute=0), missing.replace(hour=23, minute=59)])
        return down_periods


    @classmethod
    def get_curr_status_door(cls, uuid, retBatteryLevel=False):
        '''
        Returns list of status codes. See class vars

        Inputs:
        uuid (str)
        '''
        # Get down periods
        now = datetime.datetime.now()
        down_periods = cls.get_down_periods_door(uuid=uuid, start_dt=now, end_dt=now)

        ret_codes = []
        down = False
        for p in down_periods:          # Check if current time is within a down period
            # print(p)
            if p[0] <= now and now <= p[1]: 
                down = True
                break
        ret_codes.append(cls.CHECK_WARN if down else cls.OK)

        # Battery level?
        if retBatteryLevel == False: return ret_codes
        else:
            batt_lvl = []
            last_batt = sysmon_log_DAO.get_last_battery_level(uuid=uuid)
            if last_batt != None:       # Sysmon batt event found
                batt_lvl.append(last_batt.event)
                if last_batt.event < cls.batt_thresh:
                    ret_codes.append(cls.LOW_BATT)
            return ret_codes, batt_lvl


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

    @classmethod
    def get_toilet_uuid(cls, resident_id):
        '''
        WARNING: ghetto method for mid terms quick fix
        returns the active uuid (str) for the current input resident_id (int)
        '''
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()
        output = None
        query = f"SELECT uuid FROM stbern.sensor_ownership_hist WHERE resident_id = {resident_id} AND period_end IS NULL AND uuid LIKE '%m-02'"
        try:
            cursor.execute(query)
            result = cursor.fetchone()

            if result:
                output = result['uuid']
        except Exceptio as e:
            print(e)

        return output

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

    # ================== UP / DOWN ==================
    uuid = "2005-m-02"
    target = 460
    sdt = datetime.datetime(year=2018, month=3, day=2)
    edt = datetime.datetime(year=2018, month=10, day=5)

    # # MOTION =======================================
    # print("MOTION ===================================")
    # print("===== Down Periods =====")
    # down_periods = Sensor_mgmt.get_down_periods_motion(uuid=uuid, start_dt=sdt, end_dt=edt)
    # for p in down_periods: print(p)
    # print(f"Curr status: ", Sensor_mgmt.get_curr_status_motion(uuid=uuid, retBatteryLevel=True))

    # JUVO =============================================
    # sdt = datetime.datetime(year=2018, month=9, day=19, hour=12)    # Target installation pains
    # edt = datetime.datetime(year=2018, month=9, day=19, hour=16)    # Target installation pains
    # sdt = datetime.datetime(year=2018, month=3, day=2)              # MIN
    # edt = datetime.datetime(year=2018, month=10, day=5)             # MAX
    # print("JUVO ===================================")
    # print("===== Down Periods =====")
    # down_periods = Sensor_mgmt.get_down_periods_Juvo(target, sdt, edt)
    # for p in down_periods: print(p)
    # print(f"Curr status: ", Sensor_mgmt.get_curr_status_juvo(target=target))


    # DOOR =============================================
    # uuid = "2006-d-01"
    # print("DOOR ===================================")
    # print("===== Down Periods =====")
    # down_periods = Sensor_mgmt.get_down_periods_door(uuid, sdt, edt)
    # for p in down_periods: print(p)
    # print("periods done")
    # print(f"Curr status: ", Sensor_mgmt.get_curr_status_door(uuid=target, retBatteryLevel=True))

    # ALL ==============================================
    print("ALL =====================================")
    start = time.clock()
    for status in Sensor_mgmt.get_all_sensor_status_v2(retBatteryLevel=True):
        print(status)
    print("time taken: ", time.clock() - start)
