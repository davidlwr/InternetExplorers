
class Sensor(object):
    '''
<<<<<<< HEAD
    This class represents a row entry for a sensor
    '''

    uuid_tname = "uuid"
    type_tname = "type"
    location_tname = "location"
    description_tname = "description"
    juvo_target_tname = "juvo_target"

    def __init__(self, uuid, type, location, description="", juvo_target=None):
        '''
        Constructor method

        Arguments:
        uuid (str) -- i.e. "2005-m-01"
        type (str) -- "motion" | "door" | "bed sensor"
        location (str) -- "bed" | "bedroom" | "toilet"
        description (str)
        juvo_target (int) -- default None

        '''
        self.uuid = uuid
        self.type = type
        self.location = location
        self.description = description
        self.juvo_target = juvo_target
        self.var_list = [self.uuid, self.type, self.location, self.description, juvo_target]
    
=======
    This class represents a row entry for a Sensor
    '''

    uuid_tname          = "uuid"
    name_tname          = "name"
    placement_description_tname       = "placement_description"
    created_at_tname           = "created_at"
    updated_at_tname     = "updated_at"
    patient_id_tname        = "patient_id"

    def __init__(self, uuid, name, placement_description, created_at, updated_at, patient_id):

        self.uuid = uuid
        self.name = name
        self.placement_description = placement_description
        self.created_at = created_at
        self.updated_at = updated_at
        self.patient_id = patient_id

>>>>>>> origin/Jed-Graphs
    def __str__ (self):
        '''
        String representation of object
        '''
<<<<<<< HEAD
        return f"UUID:'{self.uuid}', type:'{self.type}', location:'{self.location}', desc:'{self.description}', 'juvo_target':{self.juvo_target}"
=======

        return f"Sensor - uuid: {self.uuid}, name: {self.name}, placement_description: {self.placement_description}, created_at: {self.created_at}, updated_at: {self.updated_at}, patient_id: {self.patient_id}"
>>>>>>> origin/Jed-Graphs

    def __repr__(self):
        '''
        Override python built in function to get string representation of oject
        '''
        return self.__str__()