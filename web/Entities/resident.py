
class Resident(object):
    '''
    This class represents a row entry for a resident (i.e. elderly staying at the ALFs)
    '''

    def __init__(self, name, node_id, age, fall_risk=None, status="Active", stay_location="STB", resident_id=None):
        '''
        Constructor method

        Arguments:
        name (str)          -- Patient name
        node_id (str)       -- node_id of the sensors associated with this resident
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

    
