import datetime

class Activity(object):
    '''
    This class represents an activity event created from 2 sensor_logs
    '''
    daytime_start = datetime.time(6, 30)
    daytime_end   = datetime.time(21, 30)

    def __init__(self, uuid=None, start_datetime=None, end_datetime=None, start_log=None, end_log=None):
        '''
        Constructor, object can be created either by passing all params except start_log and end_log. 
            or by passing only start_log and end_log

        Keyword arguments:
        uuid (str) -- (default None)
        start_datetime (datetime)  -- datetime obj (default None)
        end_datetime (datetime)    -- datetime obj (default None)
        start_log (Entities.sensor.log)       -- g class obj (default None)
        end_log (Entities.sensor_log)         -- Entities.log class obj (default None)
        '''

        if start_log == None and end_log == None:   # No logs given, use start and end datetime params
            self.uuid            = uuid
            self.start_datetime  = start_datetime
            self.end_datetime    = end_datetime
            self.seconds         = (self.end_datetime - self.start_datetime).total_seconds()
        
        else:
            self.uuid            = start_log.uuid
            self.start_datetime  = start_log.recieved_timestamp
            self.end_datetime    = end_log.recieved_timestamp
            self.seconds         = (self.end_datetime - self.start_datetime).total_seconds()
        

    def in_daytime(self):
        '''
        Returns True if Activity is anywhere within the daytime period set of 06.30 > 21.30 
        '''

        obj_start = self.start_datetime.time()
        obj_end   = self.end_datetime.time()
        if obj_start >= Activity.daytime_start and obj_start <= Activity.daytime_end:
            return True 
        elif obj_end >= Activity.daytime_start and obj_start <= Activity.daytime_end:
            return True
        else:
            return False


    def __str__(self):
        '''
        Returns str representation of object
        '''
        return f"ACTIVITY: uuid: {self.uuid}, secs: {self.seconds}, start_ts: {self.start_datetime.strftime('%Y-%m-%d %H:%M:%S')}, end_ts: {self.end_datetime.strftime('%Y-%m-%d %H:%M:%S')}"


    def __repr__(self):
        '''
        Override python built in function to return string prepresentation of oject
        '''
        return self.__str__() 
        
