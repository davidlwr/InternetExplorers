import sys

if __name__ == '__main__':  sys.path.append("..")
from DAOs.connection_manager import connection_manag

class Sensor_mgmt(object):


    @staticmethod
    def get_sensor_status(uuid):
        '''
        Returns 'up' | 'down' status of sensors. 
        For new sensors, Im assuming that at least a single record is sent and thus will trigger true.
        
        Inputs:
        uuid (str) -- ie "2005-m-01"

        Return:
        True if available, False if down
        '''
        
        isFucked = False
        isDoor = False   
        isMotion = False
        if len(uuid.split("-")) != 3: isFucked = True # lol what are constraints
        elif uuid.split('-')[1] == "d": isDoor = True
        elif uuid.split('-')[1] == "m": isMotion = True
            
        curr_time = datetime.datetime.now()
        curr_time_m1d = curr_time - datetime.timedelta(days=1)

        # Shit here is for normal logic
        if isFucked:
            # get last of both sysmon and sensor_log, since format of sysmon is no longer fixed
            last_sysmons = sysmon_log_DAO.get_last_sysmon(uuid)
            if len(last_sysmons) > 0:
                sys_diff = (curr_time - last_sysmons[0].recieved_timestamp).total_seconds()
                if last_sysmons[0].key == "disconnected": return False
                elif sys_diff < (60 * 60): return False # if time since last sysmon is more than 60mins, sensor is down
                else: return True  

        elif isDoor:
            # we are assuming that the door closes at least once a day
            period_data = sensor_log_DAO.get_logs(uuid=uuid,  start_datetime=curr_time_m1d, end_datetime=curr_time)
            if len(period_data) > 0: return True
            else: return False

        elif isMotion:
            last_data = sensor_log_DAO.get_last_logs(uuid=uuid)
            if len(last_data) > 0:
                data_diff = (curr_time - last_data[0].recieved_timestamp).total_seconds()
                if data_diff < (60 * 60): return True

            last_batt = sysmon_log_DAO.get_last_battery_level(uuid=uuid)
            if len(last_batt) > 0:
                batt_sdiff = (curr_time - last_batt[0].recieved_timestamp).total_seconds()
                # If last `Battery Level` update was longer than 66 minutes. Battery check fails
                if batt_sdiff < (60 * 60 * 1.1): return True
                else: return False