import sys, datetime
from collections import defaultdict

if __name__ == '__main__':  sys.path.append("..")
from DAOs.connection_manager import connection_manager
from DAOs.sensor_log_DAO import sensor_log_DAO
from DAOs.sysmon_log_DAO import sysmon_log_DAO
from Entities.sensor import Sensor
from Entities.resident import Resident

class sensor_DAO(object):
    """
    This class handles the connection between the app and the datebase table
    """
    table_name          = "stbern.sensor"


    @staticmethod
    def get_sensors(type=None, location=None, facility=None, uuid=None):
        """
        Get Sesnors by `type` andor `location` andor `uuid` or all

        Inputs
        type (str)
        location (str)
        uuid (str)

        Returns
        list of Entity.sensor
        """
        query = f"SELECT * FROM {sensor_DAO.table_name}"

        ps = []     # param_set
        if type != None:     ps.append((Sensor.type_tname, type))
        if location != None: ps.append((Sensor.location_tname, location))
        if facility != None: ps.append(Sensor.facility_tname, facility)
        if uuid != None:     ps.append((Sensor.uuid_tname, uuid))
        
        for i in range(len(ps)):
            if i==0: query += f" WHERE  `{ps[i][0]}` = \"{ps[i][1]}\""
            else:    query += f" AND    `{ps[i][0]}` = \"{ps[i][1]}\""

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
                    sensors.append(Sensor(uuid=r[Sensor.uuid_tname], type=r[Sensor.type_tname],                 \
                                          location=r[Sensor.location_tname], facility=r[Sensor.facility_tname], \
                                          description=r[Sensor.description_tname], juvo_target=r[Sensor.juvo_target_tname]))
            return sensors
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def insert_sensor(sensor):
        """
        INSERTs a sensor entry into the database
        NOTE: only sensor.type="bed sensor" can be assigned sensor.location="bed"

        Inputs:
        sensor (Entities.sensor)
        """
        # Check exception: allow only bed sensor to be found in bed
        if (sensor.type == "bed sensor" and sensor.location != "bed") or (sensor.type != "bed sensor" and sensor.location == "bed"): 
            raise ValueError('only sensor.type=\"bed sensor\" can be assigned sensor.location=\"bed\"')

        query = f"""INSERT INTO {sensor_DAO.table_name} 
                    (`{Sensor.uuid_tname}`,`{Sensor.type_tname}`,`{Sensor.location_tname}`,
                    `{Sensor.facility_tname}`,`{Sensor.description_tname}`, `{Sensor.juvo_target_tname}`) 
                    VALUES (%s, %s, %s, %s, %s, %s)"""

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, sensor.var_list)
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def get_unregistered_uuids():
        """
        Returns all distinct uuids found in `SENSOR_LOG` but not in `SENSOR` table

        Returns
        list of str: ["uuid1",... "uuid10"]
        """
        # Get all uuids found in `SENSOR_LOG`
        senslog_uuids = sensor_log_DAO.get_all_uuids()

        # Get all uuids found in `SENSOR`
        query = f"SELECT DISTINCT(`{Sensor.uuid_tname}`) FROM {sensor_DAO.table_name}"

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            result = cursor.fetchall()

            sensor_uuids = []
            if result != None:
                for r in result:
                    sensor_uuids.append(r[Sensor.uuid_tname])
            print("sensor: ", sensor_uuids)
            print("logs:   ", senslog_uuids)
            return [uuid for uuid in senslog_uuids if uuid not in sensor_uuids]

        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)
        

    @staticmethod
    def verify_sensor(uuid):
        """
        Verifies if logs with `uuid` exist in DB tables `SENSOR_LOG` or `SYSMON_LOG`
        NOTE: this method services only the sensors transmitting via mqtt. NOT JUVO

        Inputs
        uuid (str)  -- uuid identifier of sensor
        
        Returns 
        True if pass, False if fail
        """
        # Get all logs in SENSOR_LOG with uuid
        sensorlog_DAO = sensor_log_DAO()
        min_dt, max_dt = sensorlog_DAO.set_min_max_datetime
        sensorlogs = sensorlog_DAO.get_logs(uuid=uuid, start_datetime=min_dt, end_datetime=max_dt)

        # Get all logs in SYSMON_LOG with uuid
        sysmonlogs = sysmon_log_DAO.get_all_logs(uuid=uuid)

        # check if any records exist
        if len(sensorlogs)>1 or len(sysmonlogs)>1: return True
        else: return False


    # SENSOR OWNERSHIP HISTORY ==============================================================
    soh_table_name   = "stbern.SENSOR_OWNERSHIP_HIST"
    soh_period_start = "period_start"
    soh_period_end   = "period_end"
    soh_resident_id  = "resident_id"
    soh_uuid         = "uuid"
    @staticmethod
    def insert_ownership_hist(uuid, resident_id, start_datetime):
        """
        Inserts a row of ownership history of sensor into the DB

        Inputs
        uuid (str)  -- Sensor uuid
        resident_id (int)   
        start_datetime (datetime)

        Raises
        AssertionError -- There is an open period left on the ownership table, close period before adding new owner
                       -- see sensor_DAO.close_ownership_hist()
        """
        # Check for open period / current owner exists
        rdict = sensor_DAO.get_ownership_hist(uuid=uuid)
        for ruuid,rvals in rdict.items():
            if rvals[1] == None: raise AssertionError("There is an open period left on the ownership table, close period before adding new owner")

        # Add ownership history
        query = f"""INSERT INTO {sensor_DAO.soh_table_name} ({sensor_DAO.soh_uuid}, {sensor_DAO.soh_resident_id}, {sensor_DAO.soh_period_start}, {sensor_DAO.soh_period_end}) 
                    VALUES (%s, %s, %s, %s)"""

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, [uuid, resident_id, start_datetime, None])
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def close_ownership_hist(uuid, resident_id, end_datetime=None):
        '''
        Closes an open period in the ownership table

        Inputs
        uuid (str)  -- Sensor uuid
        resident_id (int)   
        end_datetime (datetime) -- default None, closes with datetime.now()

        Raises
        AssertionError -- No period open for uuid - resident_id pair
        '''
        # Check for existing open datetime
        openPeriod = False
        rdict = sensor_DAO.get_ownership_hist(uuid=uuid, residentID=resident_id)
        for ruuid,rvals in rdict.items():
            if rvals[-1][1] == None: openPeriod = True

        if openPeriod == False: raise(AssertionError("No open period for uuid, resident_id pair. Unable to close anything"))     
        
        # Construct query
        if end_datetime == None: end_datetime = datetime.datetime.now()
        query = f"""UPDATE {sensor_DAO.soh_table_name} SET `{sensor_DAO.soh_period_end}` = %s 
                     WHERE `{sensor_DAO.soh_uuid}` = %s 
                     AND `{sensor_DAO.soh_resident_id}` = %s 
                     AND `{sensor_DAO.soh_period_end}` IS NULL"""
        feedDict = [end_datetime, uuid, resident_id]

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, feedDict) 
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def get_ownership_hist(uuid=None, residentID=None):
        '''
        Returns ownership hisotry of sensor: Which resident was using the sensor during a period

        Inputs:
        uuid (str)       -- Default None 
        residentID (int) -- Default None

        Return:
        Dict: {"uuid1": [(startdate, enddate), (datetime, datetime)],
               "uuid2": [(startdate, enddate)]}
        * NOTE: Final start and end date pairs will have NO END_DATETIME as this represents an ongoing period
        * NOTE: (startdate, enddate) are (inclusive, exclusive)
        '''
        
        queryCols = []
        queryVals = []
        if residentID != None: 
            queryCols.append(sensor_DAO.soh_resident_id)
            queryVals.append(residentID)
        if uuid != None:
            queryCols.append(sensor_DAO.soh_uuid)
            queryVals.append(uuid)

        # Construct query
        query = f"SELECT * FROM {sensor_DAO.soh_table_name} "
        for i in range(len(queryVals)):
            if i == 0: query += f" WHERE `{queryCols[i]}` = %s "
            else:      query += f" AND   `{queryCols[i]}` = %s " 
        query += f" ORDER BY `{sensor_DAO.soh_period_start}` ASC"       # Sort by start periods 

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        # Read results and return dict
        try:
            if len(queryCols) != 0: cursor.execute(query, queryVals)
            else: cursor.execute(query)

            result = cursor.fetchall()

            records = defaultdict(list)
            if result != None:
                for r in result:
                    uuid   = r[sensor_DAO.soh_uuid]
                    pStart = r[sensor_DAO.soh_period_start]
                    pEnd   = r[sensor_DAO.soh_period_end]
                    records[uuid].append((pStart, pEnd))

            return records
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


# TESTS ====================================================================================================
if __name__ == '__main__': 
    # Ownership hists
    delete = False

    # Test 01: insert
    try:
        print(sensor_DAO.insert_ownership_hist(uuid="2006-m-01", resident_id=1, start_datetime=datetime.datetime.now()))
        delete = True
        print("success insert 1")
    except: 
        print("existing test record")
        delete = True

    # test 02: get 
    print(sensor_DAO.get_ownership_hist(uuid="2006-m-01", residentID=1))
    print(sensor_DAO.get_ownership_hist(uuid="2006-m-01", residentID=None))
    print(sensor_DAO.get_ownership_hist(uuid=None, residentID=None))

    # test 03: close 
    try:
        sensor_DAO.close_ownership_hist(uuid="2006-m-01", resident_id=1, end_datetime=None)
        print("success close 1... Checking with get")
        print(sensor_DAO.get_ownership_hist(uuid="2006-m-01", residentID=1))

        sensor_DAO.close_ownership_hist(uuid="2006-m-01", resident_id=1, end_datetime=None)
        print("fail close 2: should throw exception")
    except AssertionError as e:
        print("success close 2", e)

    # end test: delete
    if delete:
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()
        try: cursor.execute(f"DELETE FROM {sensor_DAO.soh_table_name} WHERE `{sensor_DAO.soh_resident_id}` = 1 AND `{sensor_DAO.soh_uuid}` = \"2006-m-01\"")
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)