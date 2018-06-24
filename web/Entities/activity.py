import datetime

class Activity(object):

    daytime_start = datetime.time(6, 30)
    daytime_end   = datetime.time(21, 30)

    def __init__(self, sensor_location, start_log, end_log, gateway_id):
        self.sensor_location = sensor_location
        self.start_log       = start_log
        self.end_log         = end_log
        self.start_datetime  = start_log.gateway_timestamp
        self.end_datetime    = end_log.gateway_timestamp
        self.seconds         = (self.end_datetime - self.start_datetime).total_seconds()
        self.gateway_id      = gateway_id
        

    def in_daytime(self):
        '''
        Returns True if  Activity is anywhere within the daytime period set of 06.30 > 21.30 
        
        '''
        obj_start = self.start_datetime.time()
        obj_end   = self.end_datetime.time()
        if obj_start >= daytime_start and obj_start <= daytime_end:
            return True 
        elif obj_end >= daytime_start and obj_start <= daytime_end:
            return True
        else:
            return Flase


    def __str__(self):
        '''
        String representation of object
        '''

        return "ACTIVITY: sens_loc: {}, gw_id: {}, secs: {}, start_ts: {}, end_ts: {}" \
                .format(self.sensor_location, self.gateway_id, self.seconds, self.start_datetime, self.end_datetime)


    def __repr__(self):
        '''
        Override python built in function to get string prepresentation of oject
        '''
        return self.__str__() 
        


