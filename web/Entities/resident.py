
class Resident(object):
    '''
    This class represents a row entry for a resident (i.e. elderly staying at the ALFs)
    '''

    name_tname          = "name"
    node_id_tname       = "node_id"
    age_tname           = "age"
    fall_risk_tname     = "fall_risk"
    status_tname        = "status"
    stay_location_tname = "stay_location"
    resident_id_tname   = "resident_id"

    def __init__(self, name, node_id, age, fall_risk=None, status="Active", stay_location="STB", resident_id=None):
        '''
        Constructor method

        Arguments:
        name (str)          -- Patient name
        node_id (str)       -- node_id of the sensor gateway associated with this resident
        age (int)           -- age of the resident
        fall_risk (str)     -- fall risk of the resident ("High", "Mid" or "Low") OPTIONAL, default=None
        status (str)        -- whether resident is currently still staying in ALF, OPTIONAL, default="Active"
        stay_location (str) -- which ALF the resident is currently in if "Active", OPTIONAL, default="STB"
        resident_id is auto incremented, generated from insertion in db
        '''

        self.name = name
        self.node_id = node_id
        self.age = age
        self.fall_risk = fall_risk
        self.status = status
        self.stay_location = stay_location
        self.resident_id = resident_id

    
    def __str__ (self):
        '''
        String representation of object
        '''

        return f"Residen - id: {self.resident_id}, name: {self.name}, node_id: {self.node_id}, age: {self.age}, fall_risk: {self.fall_risk}, fall: {self.fall_risk}, status: {self.status}, loc: {self.stay_location}"

    def __repr__(self):
        '''
        Override python built in function to get string representation of oject
        '''
        return self.__str__()