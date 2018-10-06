import datetime, os, sys
from JuvoAPI import JuvoAPI

if __name__ == '__main__':  sys.path.append("..")
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
