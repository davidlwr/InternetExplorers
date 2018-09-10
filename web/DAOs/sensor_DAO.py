import sys, datetime
from collections import defaultdict

if __name__ == '__main__':  sys.path.append("..")
from DAOs.connection_manager import connection_manager
from Entities.sensor import Sensor
from Entities.resident import Resident

class sensor_DAO(object):
    """
    This class handles the connection between the app and the datebase table
    """
    table_name          = "stbern.SENSOR"


    @staticmethod
    def get_sensors(type=None, location=None, uuid=None):
        """
        Get Sesnors by `type` andor `location` andor `uuid` or all

        Inputs
        type (str)
        location (str)
        uuid (str)
        """
        query = f"SELECT * FROM {sensor_DAO.table_name}"

        param_set = []
        if type != None: param_set.append((Sensor.type_tname, type))
        if location != None: param_set.append((Sensor.location_tname, location))
        if uuid != None: param_set.append((Sensor.uuid_tname, uuid))

        if len(param_set) == 3:   query = query + f" WHERE `{param_set[0][0]}` = \"{param_set[0][1]}\" AND `{param_set[1][0]}` = \"{param_set[1][1]}\" AND `{param_set[2][0]}` = \"{param_set[2][1]}\"" 
        elif len(param_set) == 2: query = query + f" WHERE `{param_set[0][0]}` = \"{param_set[0][1]}\" AND `{param_set[1][0]}` = \"{param_set[1][1]}\""
        elif len(param_set) == 1: query = query + f" WHERE `{param_set[0][0]}` = \"{param_set[0][1]}\""

        print(query)

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


    # SENSOR OWNERSHIP HISTORY ==============================================================
    soh_table_name   = "stbern.SENSOR_OWNERSHIP_HIST"
    soh_period_start = "period_start"
    soh_resident_id  = "resident_id"
    soh_uuid         = "uuid"
    @staticmethod
    def get_ownership_hist(residentID):
        """
        Returns ownership hisotry of sensor: Which resident was using the sensor during a period

        Inputs:
        residentID (int)

        Return:
        Dict: {"uuid1": [(startdate, enddate), (datetime, datetime)],
               "uuid2": [(startdate, enddate)]}
        * NOTE: (startdate, enddate) are (inclusive, exclusive)
        """
        query = f"SELECT * FROM {sensor_DAO.soh_table_name} WHERE `{sensor_DAO.soh_resident_id}` = %s ORDER BY '{sensor_DAO.soh_period_start}' DESC"

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, [residentID])
            result = cursor.fetchall()

            records = []
            if result != None:
                for r in result:
                    records.append((r[sensor_DAO.soh_uuid], r[sensor_DAO.soh_period_start]))
            
            # Create and populate dict
            rdict = defaultdict(list)
            if len(records) > 1:
                for i in range(len(records)-1):
                    uuid, period_start = records[i]
                    tuuid, period_end  = records[i+1]

                    rdict[uuid].append(period_start, period_end)

                # Convert last record to period of: record ---- curr datetime
                uuid, period_start = records[-1]
                rdict[uuid].append(period_start, datetime.datetime.now())

            return rdict
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

    ss = sensor_DAO.get_sensors(type="motion")
    for s in ss: print(f"ss 1 mot:{s}")

    ss = sensor_DAO.get_sensors(location="bed")
    for s in ss: print(f"ss 1 loc:{s}")

    ss = sensor_DAO.get_sensors(uuid="2005-m-01")
    for s in ss: print(f"ss 1 uid:{s}")

    ss = sensor_DAO.get_sensors(type="motion", location="bedroom", uuid="2005-m-01")
    for s in ss: print(f"ss 3:{s}")
    
    # sensor_DAO.insert_type("test")
    ts = sensor_DAO.get_types()
    for s in ts: print(f"type:{s}")

    # sensor_DAO.insert_location("test")
    ls = sensor_DAO.get_locations()
    for s in ls: print(f"locs:{s}")

    # sensor_DAO.insert_facilities(abrv="t", fullname="test", description="TESTTEST")
    fs = sensor_DAO.get_facilities()
    for s in fs: print(f"faci:{s}")