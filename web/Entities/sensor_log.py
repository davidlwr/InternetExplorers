import datetime

class Sensor_Log(object):
    '''
    This class represents a row entry of the DB table "SENSOR_LOG"
    '''

    # Table col names
    uuid_tname                = 'uuid'
    node_id_tname             = 'node_id'
    event_tname               = 'event'
    recieved_timestamp_tname  = 'recieved_timestamp'

    def __init__(self, uuid, node_id, event, recieved_timestamp):
        '''
        Constructor method

        Inputs:
        uuid (str)    -- Sensor identifier
        node_id (int) -- 
        event (int)   -- value of event
        recieved_timestamp (datetime) -- time consumer recieved message
        '''

        self.uuid = uuid
        self.node_id = node_id
        self.event = event
        self.recieved_timestamp = recieved_timestamp

        self.var_list = [self.uuid, self.node_id, self.event, self.recieved_timestamp.strftime('%Y-%m-%d %H:%M:%S')]


    def __str__ (self):
        '''
        String representation of object
        '''

        return f"Sensor_Log - uuid: {self.uuid}, node_id: {self.node_id}, event: {self.event}, recieved_timestamp: {self.recieved_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


    def __repr__(self):
        '''
        Override python built in function to get string representation of oject
        '''
        return self.__str__()
