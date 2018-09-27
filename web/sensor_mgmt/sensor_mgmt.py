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
    def get_sensor_status(cls, uuid):
        '''
        Returns 'up' | 'down' status of sensors. 
        For new sensors, Im assuming that at least a single record is sent and thus will trigger true.
        
        Inputs:
        uuid (str)

        Return:
        See list of status codes 
        '''
        # AREAS OF IMPROVEMENT
        # 1. Juvo Bed sensor: Warning triggered if no sleep in the past sleep period 9pm-9am. What about if sleep = 1sec? May also be a problem with elderly
        #   - Maybe look at the breakdown period would be better >> light, deep, awake that kind of thing
        # 2. What if sensor partially breaks, sysmon sends, but no sensor logs? Dont think this can be detected also
        ret_codes = []

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

            # Check2: Battery level
            last_batt = sysmon_log_DAO.get_last_battery_level(uuid=uuid)
            if last_batt.event < cls.batt_thresh: ret_codes.append(cls.LOW_BATT)


        elif isMotion:  # MOTION SENSOR
            last_batt = sysmon_log_DAO.get_last_battery_level(uuid=uuid)
            print("\t last batt: ", last_batt)
            if last_batt != None:
                batt_update_period = (curr_time - last_batt.recieved_timestamp).total_seconds()

                # Check 1: hourly battery update. aeotec multisensor 6 should send battery level sysmon updates on the hour
                # This may just be Boon Thais' configs
                if batt_update_period > (60 * 60 * 1.2): ret_codes.append(cls.CHECK_WARN)
                else: ret_codes.append(cls.OK)

                # Check 2: Low battery 
                if last_batt.event < cls.batt_thresh: ret_codes.append(cls.LOW_BATT)


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
        
        return ret_codes


# TESTS ======================================================================================
if __name__ == '__main__': 
    
    uuid = "2005-m-01"
    print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    uuid = "2005-m-02"
    print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    uuid = "2005-d-01"
    print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    uuid = "2005-d-02"
    print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")

    uuid = "2005-j-01"
    print(f"Testing UUID: {uuid}, Status: {Sensor_mgmt.get_sensor_status(uuid)}")


