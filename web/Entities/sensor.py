
class Sensor(object):
    '''
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

    def __str__ (self):
        '''
        String representation of object
        '''

        return f"Sensor - uuid: {self.uuid}, name: {self.name}, placement_description: {self.placement_description}, created_at: {self.created_at}, updated_at: {self.updated_at}, patient_id: {self.patient_id}"

    def __repr__(self):
        '''
        Override python built in function to get string representation of oject
        '''
        return self.__str__()