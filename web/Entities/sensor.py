
class Sensor(object):
    '''
    This class represents a row entry for a sensor
    '''
    uuid_tname          = "uuid"
    type_tname          = "type"            # See TYPE table
    location_tname      = "location"        # See LOCATION table
    facility_tname      = "facility_abrv"   # See FACILITY table
    description_tname   = "description"     # General description of location within facility
    juvo_target_tname   = "juvo_target"     # unique ID of Juvo, used by Juvo API

    def __init__(self, uuid, type, location, facility, description="", juvo_target=None):
        '''
        Constructor method

        Arguments:
        uuid (str)      -- i.e. "2005-m-01"
        type (str)      -- "motion" | "door" | "bed sensor"
        location (str)  -- "bed" | "bedroom" | "toilet"
        facility (str)  -- Based on FACILITY table
        description (str)
        juvo_target (int) -- default None
        '''
        self.uuid = uuid
        self.type = type
        self.location = location
        self.facility = facility
        self.description = description
        self.juvo_target = juvo_target
        self.var_list = [self.uuid, self.type, self.location, self.facility, self.description, self.juvo_target]
    
    def __str__ (self):
        '''
        String representation of object
        '''
        return f"UUID:'{self.uuid}', type:'{self.type}', loc:'{self.location}', faci'{self.facility}', desc:'{self.description}', 'juvo_target':{self.juvo_target}"

    def __repr__(self):
        '''
        Override python built in function to get string representation of oject
        '''
        return self.__str__()