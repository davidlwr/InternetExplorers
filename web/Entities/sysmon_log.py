import datetime

class Sysmon_Log(object):
    '''
    This class represents a row entry of the DB table 'SYSMON_LOG'
    '''

    # Table col names
    uuid_tname               = "uuid"
    node_id_tname            = "node_id"
    event_tname              = "event"
    key_tname                = "key"
    recieved_timestamp_tname = "recieved_timestamp"

    # write param defs
    def __init__(self, uuid, node_id, event, key, recieved_timestamp):
        '''
        Constructor method

        Input:
        uuid (str)
        node_id (int)
        event (float)
        key (str)
        recieved_timestamp (datetime)
        '''        
        self.uuid               = uuid
        self.node_id            = node_id
        self.event              = event
        self.key                = key
        self.recieved_timestamp = recieved_timestamp

        self.varlist = [self.uuid, self.node_id, self.event, self.key, self.recieved_timestamp]


    def __str__(self):
        '''
        String representation of object
        '''
        return f"SYSMONLOG: uuid: {self.uuid}, node_id: {self.node_id}, event: {self.event}, key: {self.key}, timestamp: {self.recieved_timestamp}"

    def __repr__(self):
        '''
        Override python built in function to get string representation of oject
        '''
        return self.__str__()

