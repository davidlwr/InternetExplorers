from datetime import timedelta


class Shift_log(object):
    '''
    This class represents a row entry in the DB table for 'SHIFT_LOG'
    '''

    datetime_tname = "datetime"
    patient_id_tname = "patient_id"
    num_falls_tname = "num_falls"
    num_near_falls_tname = "num_near_falls"
    food_consumption_tname = "food_consumption"
    num_toilet_visit_tname = "num_toilet_visit"
    temp_tname = "temp"
    sbp_tname = "sbp"
    dbp_tname = "sbp"
    pulse_tname = "pulse"

    FOOD_CONSUMPTION_MAPPING = {0: "Insufficient",
                                1: "Moderate",
                                2: "Excessive"}

    def __init__(self, date=None, day_night=None, patient_id=None, num_falls=None, num_near_falls=None,
                 food_consumption=None, num_toilet_visit=None, temp=None, sbp=None, dbp=None, pulse=None):
        '''
        Constructor
        
        Keyword arguments
        datetime (datetime)    -- default None
        day_night (int)     -- default None
        patient_id (int)       -- default None
        num_falls (int)        -- default None
        num_near_falls (int)   -- default None
        food_consumption (int) -- see class var 'FOOD_CONSUMPTION_MAPPING' (default None)
        num_toilet_visit (int) -- default None
        temp (float)       -- default None
        sbp (float)      -- default None
        dbp (float)      -- default None
        pulse (float)      -- default None
        '''

        datetime = date.strftime('%Y-%m-%d')
        if day_night == 1:
            datetime += " 12:00:00"
        else:
            datetime += " 20:00:00"

        self.datetime = datetime
        self.patient_id = patient_id
        self.num_falls = num_falls
        self.num_near_falls = num_near_falls
        self.food_consumption = food_consumption
        self.num_toilet_visit = num_toilet_visit
        self.temp = temp
        self.sbp = sbp
        self.dbp = dbp
        self.pulse = pulse

        self.var_list = [self.datetime, self.patient_id, self.num_falls, \
                         self.num_near_falls, self.food_consumption, self.num_toilet_visit, self.temp,
                         self.sbp, self.dbp, self.pulse]

    def __str__(self):
        '''
        String representation of object
        '''
        return f"""SHIFT LOG: datetime: {self.datetime}, patient_id: {self.patient_id},
                num_falls: {self.num_falls}, num_near_falls: { self.num_near_falls}, food_consumption: {self.food_consumption},
                num_toilet_visit: {self.num_toilet_visit}, temp: {self.temp}, sbp: {self.sbp}, dbp: {self.dbp}, pulse: {self.pulse}"""

    def __repr__(self):
        '''
        Override python built in function to get string representation of oject
        '''
        return self.__str__()
