

class Shift_log(object):

    '''
    This class represents a row entry in the DB table for 'SHIFT_LOG'
    '''

    datetime_tname         = "datetime"
    patient_id_tname       = "patient_id"
    num_falls_tname        = "num_falls"
    num_near_falls_tname   = "num_near_falls"
    food_consumption_tname = "food_consumption"
    num_toilet_visit_tname = "num_toilet_visit"
    temp_3pm_tname         = "temp_3pm"
    bp_weekly_tname        = "bp_weekly"
    bpm_tname              = "bpm"

    FOOD_CONSUMPTION_MAPPING = {0: "Insufficient",
                                1: "Moderate",
                                2: "Excessive"}

    def __init__(self, datetime=None, patient_id=None, num_falls=None, num_near_falls=None, food_consumption=None, num_toilet_visit=None, temp_3pm=None, bp_weekly=None, bpm=None):
        '''
        Constructor
        
        Keyword arguments
        datetime (datetime)    -- default None
        patient_id (int)       -- default None
        num_falls (int)        -- default None
        num_near_falls (int)   -- default None
        food_consumption (int) -- see class var 'FOOD_CONSUMPTION_MAPPING' (default None)
        num_toilet_visit (int) -- default None
        temp_3pm (float)       -- default None
        bp_weekly (float)      -- default None
        bpm (int)              -- defauly None
        '''
        self.datetime         = datetime
        self.patient_id       = patient_id
        self.num_falls        = num_falls
        self.num_near_falls   = num_near_falls
        self.food_consumption = food_consumption
        self.num_toilet_visit = num_toilet_visit
        self.temp_3pm         = temp_3pm
        self.bp_weekly        = bp_weekly
        self.bpm              = bpm

        self.var_list = [self.datetime, self.patient_id, self.num_falls, \
                         self.num_near_falls, self.food_consumption, self.num_toilet_visit, self.temp_3pm, self.bp_weekly, self.bpm]


    def __str__(self):
        '''
        String representation of object
        '''
        return f"""SHIFT LOG: datetime: {self.datetime.strftime('%Y-%m-%d %H:%M:%S')}, patient_id: {self.patient_id},
                num_falls: {self.num_falls}, num_near_falls: { self.num_near_falls}, food_consumption: {self.food_consumption},
                num_toilet_visit: {self.num_toilet_visit}, temp_3pm: {self.temp_3pm}, bp_weekly: {self.bp_weekly}, bpm: {self.bpm}"""

    def __repr__(self):
        '''
        Override python built in function to get string representation of oject
        '''
        return self.__str__()