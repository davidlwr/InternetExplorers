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
    table_name = "stbern.sensor"
    @staticmethod
    def get_location_by_node_id(node_id):
        query = f"SELECT location FROM {sensor_DAO.table_name} where uuid = %s"
  
        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, (node_id, ))
            results = cursor.fetchall()
            if results: return results
            else: return []
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)
    @staticmethod
    def get_type_by_node_id(node_id):
        query = f"SELECT type FROM {sensor_DAO.table_name} where uuid = %s"
  
        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, (node_id, ))
            results = cursor.fetchall()
            if results: return results
            else: return []
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)

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

        ps = []  # param_set
        if type != None:     ps.append((Sensor.type_tname, type))
        if location != None: ps.append((Sensor.location_tname, location))
        if facility != None: ps.append(Sensor.facility_tname, facility)
        if uuid != None:     ps.append((Sensor.uuid_tname, uuid))

        for i in range(len(ps)):
            if i == 0:
                query += f" WHERE  `{ps[i][0]}` = \"{ps[i][1]}\""
            else:
                query += f" AND    `{ps[i][0]}` = \"{ps[i][1]}\""

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
                    sensors.append(Sensor(uuid=r[Sensor.uuid_tname], type=r[Sensor.type_tname], \
                                          location=r[Sensor.location_tname], facility=r[Sensor.facility_tname], \
                                          description=r[Sensor.description_tname],
                                          juvo_target=r[Sensor.juvo_target_tname]))
            return sensors
        except:
            raise
        finally:
            factory.close_all(cursor=cursor, connection=connection)

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
        except:
            raise
        finally:
            factory.close_all(cursor=cursor, connection=connection)

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
        if len(sensorlogs) > 1 or len(sysmonlogs) > 1:
            return True
        else:
            return False

    # SENSOR OWNERSHIP HISTORY ==============================================================
    soh_table_name   = "stbern.sensor_ownership_hist"
    soh_period_start = "period_start"
    soh_period_end = "period_end"
    soh_resident_id = "resident_id"
    soh_uuid = "uuid"

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
        for ruuid, rvals in rdict.items():
            if rvals[1] == None: raise AssertionError(
                "There is an open period left on the ownership table, close period before adding new owner")

        # Add ownership history
        query = f"""INSERT INTO {sensor_DAO.soh_table_name} ({sensor_DAO.soh_uuid}, {sensor_DAO.soh_resident_id}, {sensor_DAO.soh_period_start}, {sensor_DAO.soh_period_end})
                    VALUES (%s, %s, %s, %s)"""

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, [uuid, resident_id, start_datetime, None])
        except:
            raise
        finally:
            factory.close_all(cursor=cursor, connection=connection)

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
        for ruuid, rvals in rdict.items():
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
    def get_ownership_hist(uuid=None, residentID=None, type=None, start_dt=None, end_dt=None):
        '''
        Returns ownership hisotry of sensor: Which resident was using the sensor during a period

        Inputs:
        uuid (str)          -- Default None 
        residentID (int)    -- Default None
        type (str)          -- Default None, sensor type
        start_dt (datetime) -- Default None Returns all periods within or overlapping the given start and end dts
        end_dt (datetime)   -- Default None

        Return:
        Dict: {"uuid1": [(residentID, startdate, enddate), (residentID, datetime, datetime)],
               "uuid2": [(residentID, startdate, None)]}
        * NOTE: Final start and end date pairs will have 'None' END_DATETIME as this represents an ongoing period
        * NOTE: (startdate, enddate) are (inclusive, exclusive)
        '''

        queryVals = []
        # Construct query
        #stbern.sensor_ownership_hist as t1 inner join stbern.sensor as t2 on t1.uuid = t2.uuid
        query = f"SELECT * FROM {sensor_DAO.soh_table_name} AS t1 INNER JOIN {sensor_DAO.table_name} AS t2 ON t1.uuid = t2.uuid "

        prefix = None
        if residentID != None:
            prefix = "WHERE" if prefix==None else "AND"
            query += f" {prefix} t1.`{sensor_DAO.soh_resident_id}` = %s "
            queryVals.append(residentID)

        if uuid != None:
            prefix = "WHERE" if prefix==None else "AND"
            query += f" {prefix} t1.`{sensor_DAO.soh_uuid}` = %s "
            queryVals.append(uuid)
            
        if type != None:
            prefix = "WHERE" if prefix==None else "AND"
            query += f" {prefix} t1.`{sensor_DAO.soh_uuid}` = %s "
            queryVals.append(type)
        
        if start_dt != None: 
            prefix = "WHERE" if prefix==None else "AND"
            query += f" {prefix} t1.`{sensor_DAO.soh_period_end}` > \"{start_dt.strftime('%Y-%m-%d %H:%M:%S')}\" "
            prefix = " AND "
        
        if end_dt != None:
            query += f" {prefix} (`{sensor_DAO.soh_period_start}` IS NULL OR `{sensor_DAO.soh_period_start}` < \"{end_dt.strftime('%Y-%m-%d %H:%M:%S')}\")"

        query += f" ORDER BY `{sensor_DAO.soh_period_start}` ASC"       # Sort by start periods 

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        # Read results and return dict
        try:
            cursor.execute(query, queryVals)

            result = cursor.fetchall()

            records = defaultdict(list)
            if result != None:
                for r in result:
                    rid    = r[sensor_DAO.soh_resident_id]
                    uuid   = r[sensor_DAO.soh_uuid]
                    pStart = r[sensor_DAO.soh_period_start]
                    pEnd = r[sensor_DAO.soh_period_end]
                    records[uuid].append((rid, pStart, pEnd))
            return records
        except:
            raise
        finally:
            factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def get_current_owner(uuid):
        '''
        Get current owner of the sensor, returns a resident id

        Inputs:
        uuid (str)

        Returns:
        A (int) residentID or None if no current owner found
        '''

        r_dict = sensor_DAO.get_ownership_hist(uuid=uuid)
        l_hist = r_dict[uuid]

        # Check if any ownership records exist
        if len(l_hist) == 0: return None

        # Check if any open period exists
        last_ownership = l_hist[-1]         # (residentID, startDt, endDt)
        rid = last_ownership[0]
        edt = last_ownership[2]
        if edt == None: return rid          # Empty end datetime found, this is an ongoing period
        else: return None                   # Existing end datetime found, this is a closed period


    @staticmethod
    def assign_ownerless_to_noone(ownership_list, start_dt=None, end_dt=None):
        '''
        Utility method to assign empty ownerless periods to no one of -1
        This creates a list of continuous periods

        Inputs: 
        onwership_list (list) -- [[rid, startdt, enddt] ,...]
        start_dt (datetime) -- Filters out values < start_dt. Default None
        end_dt (datetiem) -- Filters out values > end_dt. Default None
        '''

        # Filter out periods not within the start and end dts given
        if start_dt != None: ownership_list = [[rid,sdt,edt] for rid,sdt,edt in ownership_list if edt > start_dt]   # Filter by start_dt
        if end_dt   != None: ownership_list = [[rid,sdt,edt] for rid,sdt,edt in ownership_list if sdt < end_dt]     # Filter by end_dt

        ownership_list = ownership_list.sorted(key = lambda x: x[1])    # asccending order
        
        # Replace start and end periods with the limiting start_dt and/or end_dt
        if start_dt != None: ownership_list[0][1]  = start_dt
        if end_dt   != None: ownership_list[-1][2] = end_dt

        #   Filling in ownerless periods
        ownerless_periods = []
        prev_sdt = None
        prev_edt = None
        for rid,sdt,edt in ownership_list:
            # Initial assignment
            if prev_sdt!=None and prev_edt!=None and ((sdt-prev_edt) > 0): 
                # There is a gap between ownerships, therefore assign to no one -1
                ownerless_periods.append(-1, prev_edt, sdt)
            prev_sdt, prev_edt = sdt, edt

        ret_list = ownerless_periods + ownerless_periods     # combine ownerless periods and ownershiplist
        ret_list.sort(key = lambda x: x[1], reversed=False)  # resort by date
        
        return ret_list    


    # TYPES =================================================================================
    type_table_name     = "stbern.sensor_type"
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
        except:
            raise
        finally:
            factory.close_all(cursor=cursor, connection=connection)


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
        except:
            raise
        finally:
            factory.close_all(cursor=cursor, connection=connection)

    # LOCATIONS ==============================================================================
    location_table_name = "stbern.sensor_location"
    location_col_name = "location"

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
        except:
            raise
        finally:
            factory.close_all(cursor=cursor, connection=connection)

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
        except:
            raise
        finally:
            factory.close_all(cursor=cursor, connection=connection)

    # FACILITYS ==============================================================================
    facility_table_name     = "stbern.facility"
    facility_abrv_cname     = "abrv"
    facility_fullname_cname = "fullname"
    facility_desc_cname = "description"

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
                    facilities.append((r[sensor_DAO.facility_abrv_cname], \
                                       r[sensor_DAO.facility_fullname_cname], \
                                       r[sensor_DAO.facility_desc_cname]))
            return facilities
        except:
            raise
        finally:
            factory.close_all(cursor=cursor, connection=connection)


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
        except:
            raise
        finally:
            factory.close_all(cursor=cursor, connection=connection)

    @staticmethod
    def get_juvo_resident_ids(location_filter='bkttm'):
        '''
        Returns list of resident_id for residents with juvo bed sensors

        Not implemented: filter by ALF location
        '''
        output = []
        try:
            query = f"SELECT {sensor_DAO.soh_resident_id} FROM {sensor_DAO.soh_table_name} WHERE {sensor_DAO.soh_uuid} IN (SELECT {Sensor.uuid_tname} FROM {sensor_DAO.table_name} WHERE {Sensor.juvo_target_tname} is not Null)"
            factory = connection_manager()
            connection = factory.connection
            cursor = connection.cursor()

            cursor.execute(query)
            result = cursor.fetchall()

            if result:
                for r in result:
                    output.append(r['resident_id'])
        except Exception as e:
            print(e)

        return output

    @staticmethod
    def get_juvo_target_from_resident_id(_resident_id, date_in_use=None):
        '''
        Returns the juvo target (int) in use at the current time for the input resident id (int)

        TODO: optional input to get juvo target at another point in time
        '''
        output = 0

        query = f"SELECT {Sensor.juvo_target_tname} FROM {sensor_DAO.table_name} WHERE {Sensor.uuid_tname} IN (SELECT {sensor_DAO.soh_uuid} FROM {sensor_DAO.soh_table_name} WHERE {sensor_DAO.soh_resident_id} = {_resident_id} AND {sensor_DAO.soh_uuid} LIKE '%-j-%' AND {sensor_DAO.soh_period_end} is Null)"
        try:
            factory = connection_manager()
            connection = factory.connection
            cursor = connection.cursor()

            cursor.execute(query)
            result = cursor.fetchone()
            if result:
                output = result[Sensor.juvo_target_tname]
        except Exception as e:
            print(e)

        return output

    @staticmethod
    def get_unregistered_motion_door_sensors():
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

        except:
            raise
        finally:
            factory.close_all(cursor=cursor, connection=connection)


# TESTS ====================================================================================================
# if __name__ == '__main__':
    # # Ownership hists
    delete = True

    # # Test 01: insert
    # try:
    #     print(sensor_DAO.insert_ownership_hist(uuid="2006-m-01", resident_id=1, start_datetime=datetime.datetime.now()))
    #     delete = True
    #     print("success insert 1")
    # except:
    #     print("existing test record")
    #     delete = True

    # # test 02: get
    # print(sensor_DAO.get_ownership_hist(uuid="2006-m-01"))
    # print(sensor_DAO.get_ownership_hist(uuid="2006-m-01", residentID=None))
    # print(sensor_DAO.get_ownership_hist(uuid=None, residentID=None))

    # # test 03: close
    # try:
    #     sensor_DAO.close_ownership_hist(uuid="2006-m-01", resident_id=1, end_datetime=None)
    #     print("success close 1... Checking with get")
    #     print(sensor_DAO.get_ownership_hist(uuid="2006-m-01", residentID=1))

    #     sensor_DAO.close_ownership_hist(uuid="2006-m-01", resident_id=1, end_datetime=None)
    #     print("fail close 2: should throw exception")
    # except AssertionError as e:
    #     print("success close 2", e)

    # # end test: delete
    # if delete:
    #     factory = connection_manager()
    #     connection = factory.connection
    #     cursor = connection.cursor()
    #     try: cursor.execute(f"DELETE FROM {sensor_DAO.soh_table_name} WHERE `{sensor_DAO.soh_resident_id}` = 1 AND `{sensor_DAO.soh_uuid}` = \"2006-m-01\"")
    #     except: raise
    #     finally: factory.close_all(cursor=cursor, connection=connection)
