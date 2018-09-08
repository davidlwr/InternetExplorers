
class Sensor(object):
    '''
    This class represents a row entry for a sensor
    '''

    uuid_tname = "uuid"
    type_tname = "type"
    locaiton_tname = "location"
    description_tname = "description"

    def __init__(self, uuid, type, location, description=""):
        '''
        Constructor method

        Arguments:
        uuid (str) -- i.e. "2005-m-01"
        type (str) -- "motion" | "door" | "bed sensor"
        location (str) -- "bed" | "bedroom" | "toilet"
        description (str)
        '''
        self.uuid = uuid
        self.type = type
        self.location = location
        self.description = description
        self.var_list = [self.uuid, self.type, self.location, self.description]

    
    def __str__ (self):
        '''
        String representation of object
        '''
        return f"UUID:'{self.uuid}', type:'{self.type}', location:'{self.location}', desc:'{self.description}'"

    def __repr__(self):
        '''
        Override python built in function to get string representation of oject
        '''
        return self.__str__()