import datetime
import pandas as pd

class Log(object):
    '''
    This class represents a row entry of the DB tables for BOTH 'SENSOR_LOG' and 'SYSMON_LOG'

    Class static variables:
    sensor_id_tname         = "sensor_id"
    sensor_location_tname   = "sensor_location"
    gateway_id_tname        = "gateway_id"
    gateway_timestamp_tname = "gateway_timestamp"
    key_tname               = "key"
    reading_type_tname      = "reading_type"
    server_timestamp_tname  = "server_timestamp"
    value_tname             = "value"

    '''

    # Table col names
    sensor_id_tname         = "sensor_id"
    sensor_location_tname   = "sensor_location"
    gateway_id_tname        = "gateway_id"
    gateway_timestamp_tname = "gateway_timestamp"
    key_tname               = "key"
    reading_type_tname      = "reading_type"
    server_timestamp_tname  = "server_timestamp"
    value_tname             = "value"

    # write param defs
    def __init__(self, sensor_id=None, sensor_location=None, gateway_id=None,   \
                gateway_timestamp=None, key=None, reading_type=None,            \
                server_timestamp=None, value=None):
        '''
        Constructor method

        Keyword arguments:
        sensor_id         -- (default None)
        sensor_location   -- (default None)
        gateway_id        -- (default None)
        gateway_timestamp -- (default None)
        key               -- (default None)
        reading_type      -- (default None)
        server_timestamp  -- (default None)
        value             -- (default None)
        '''        
        self.sensor_id         = sensor_id
        self.sensor_location   = sensor_location
        self.gateway_id        = gateway_id
        self.gateway_timestamp = gateway_timestamp
        self.key               = key
        self.reading_type      = reading_type
        self.server_timestamp  = server_timestamp
        self.value             = value


    def datetime_to_date(self, date_time):
        '''
        changes datetime to date only
        '''
        return original_date.replace(hour=0, minute=0, second=0, microsecond=0)


    def __str__(self):
        '''
        String representation of object
        '''
        return "LOG: sens_id: {}, sens_loc: {}, gw_id: {}, gw_ts: {}, value: {}" \
                .format(self.sensor_id, self.sensor_location, self.gateway_id, self.gateway_timestamp, self.value)


    def __repr__(self):
        '''
        Override python built in function to get string representation of oject
        '''
        return self.__str__()

# print(Log.sensor_id_tname)