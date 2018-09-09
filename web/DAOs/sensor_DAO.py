import sys

if __name__ == '__main__':  sys.path.append("..")
from DAOs.connection_manager import connection_manager
from Entities.sensor import Sensor

class sensor_DAO(object):
    """
    This class handles the connection between the app and the datebase table
    """
    table_name          = "stbern.SENSOR"


    @staticmethod
    def get_sensors(type=None, location=None):
        """
        Get Sesnors by `type` and `location`

        Inputs
        type (str)
        location (str)
        """
        query = f"SELECT * FROM {sensor_DAO.table_name}"

        param_set = []
        if type != None: param_set.append((Sensor.type_tname, type))
        if location != None: param_set.append((Sensor.location_tname, location))

        if len(param_set) == 2: query + f" WHERE `{param_set[0][0]}` = \"{param_set[0][1]}\" AND `{param_set[1][0]}` = \"{param_set[1][1]}\""
        elif len(param_set) == 1: query + f" WHERE `{param_set[0][0]}` = \"{param_set[0][1]}\""

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            result = cursor.fetchall()

            sensors = []
            if result != None:
                for r in result:
                    sensors.append(Sensor(uuid=r[Sensor.uuid_tname], type=r[Sensor.type_tname], location=r[Sensor.location_tname], \
                                          description=r[Sensor.description_tname], juvo_target=r[Sensor.juvo_target_tname]))
            return sensors
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def insert_sensor(sensor):
        """
        INSERTs a sensor entry into the database

        Inputs:
        sensor (Entities.sensor)
        """
        query = f"INSERT INTO {sensor_DAO.table_name} (`uuid`,`type`,`location`,`description`) VALUES (%s, %s, %s, %s)"

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, sensor.var_list)
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    # TYPES =================================================================================
    type_table_name     = "stbern.SENSOR_TYPE"
    type_col_name       = "type"
    @staticmethod
    def get_types():
        """
        Returns a list of str, of all sensor types. i.e. "motion", "bed sensor"..etc
        """
        query = f"SELECT `{sensor_DAO.type_col_name}` FROM {sensor_DAO.type_table_name}"

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            result = cursor.fetchall()

            types = []
            if result != None:
                for r in result:
                    types.append(r[sensor_DAO.type_col_name])
            return types
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)
        

    @staticmethod
    def insert_type(type):
        """
        Inserts a type into the type table... 
        Technically should not be used in the front end, unless you wanna implement some gross logic

        Inputs
        type (str)
        """
        query = f"INSERT INTO {sensor_DAO.type_table_name} (`{sensor_DAO.type_col_name}`) VALUES (%s)"

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, [type])
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    # LOCATIONS ==============================================================================
    location_table_name = "stbern.SENSOR_LOCATION"
    location_col_name   = "location"
    @staticmethod
    def get_locations():
        """
        Returns a list of str, of all sensor types. i.e. "motion", "bed sensor"..etc
        """
        query = f"SELECT `{sensor_DAO.location_col_name}` FROM {sensor_DAO.location_table_name}"

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            result = cursor.fetchall()

            locations = []
            if result != None:
                for r in result:
                    locations.append(r[sensor_DAO.location_col_name])
            return locations
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def insert_location(location):
        """
        Inserts a type into the type table... 
        Technically should not be used in the front end, unless you wanna implement some gross logic

        Inputs
        location (str)
        """
        query = f"INSERT INTO {sensor_DAO.location_table_name} (`{sensor_DAO.location_col_name}`) VALUES (%s)"

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, [location])
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    # FACILITYS ==============================================================================
    facility_table_name     = "stbern.FACILITY"
    facility_abrv_cname     = "abrv"
    facility_fullname_cname = "fullname"
    facility_desc_cname     = "description"
    @staticmethod
    def get_facilities():
        """
        Returns all facilities in the database

        Returns
        list of params in form: [("abrv", "fullname", "description")]
        """
        query = f"SELECT * FROM {sensor_DAO.facility_table_name}"

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            result = cursor.fetchall()

            facilities = []
            if result != None:
                for r in result:
                    facilities.append((r[sensor_DAO.facility_abrv_cname],       \
                                        r[sensor_DAO.facility_fullname_cname],  \
                                        r[sensor_DAO.facility_desc_cname]))
            return facilities
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)
    

    @staticmethod
    def insert_facilities(abrv, fullname, description=""):
        """
        Inserts a record of facility into the database

        Inputs
        abrv (str) -- Abreviation
        fuyllname (str)
        description (str) -- Default ""
        """
        query = f"INSERT INTO {sensor_DAO.facility_table_name} (`{sensor_DAO.facility_abrv_cname}`,`{sensor_DAO.facility_fullname_cname}`,`{sensor_DAO.facility_desc_cname}`) VALUES (%s, %s, %s)"

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, [abrv, fullname, description])
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


if __name__ == '__main__': 
    ss = sensor_DAO.get_sensors()
    for s in ss: print(f"sensor:{s}")
    
    # sensor_DAO.insert_type("test")
    ts = sensor_DAO.get_types()
    for s in ts: print(f"type:{s}")

    # sensor_DAO.insert_location("test")
    ls = sensor_DAO.get_locations()
    for s in ls: print(f"locs:{s}")

    # sensor_DAO.insert_facilities(abrv="t", fullname="test", description="TESTTEST")
    fs = sensor_DAO.get_facilities()
    for s in fs: print(f"faci:{s}")