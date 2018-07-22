import datetime

class Sysmon_Log(object):
    '''
    This class represents a row entry of the DB table 'SYSMON_LOG'

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
    def __init__(self, sensor_id, gateway_id, reading_type, value, sensor_location=None,   \
                gateway_timestamp=None, key=None, server_timestamp=None):
        '''
        Constructor method

        Keyword arguments:
        sensor_id         -- 
        gateway_id        -- 
        reading_type      --
        value             -- 
        sensor_location   -- str, location description (default None)
        gateway_timestamp -- Datetime obj (default None)
        key               -- (default None)
        server_timestamp  -- datetime obj (default None)
        
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
        return date_time.replace(hour=0, minute=0, second=0, microsecond=0)


    def __str__(self):
        '''
        String representation of object
        '''
        return f"LOG: sens_id: {self.sensor_id}, sens_loc: {self.sensor_location}, gw_id: {self.gateway_id}, gw_ts: {self.gateway_timestamp.strftime('%Y-%m-%d %H:%M:%S')}, value: {self.value}"


    def __repr__(self):
        '''
        Override python built in function to get string representation of oject
        '''
        return self.__str__()

