import datetime, os
from connection_manager import connection_manager
import sys
sys.path.append("..")
from Entities.log import Log
from Entities.activity import Activity

class sensor_log_DAO(object):
    '''
    This class handles the connection between the app and the datebase table
    '''

    table_name = "stbern.SENSOR_LOG"

    def __init__(self):
        '''
        initialize by setting descriptive vars
        '''
        self.max_datetime = None
        self.min_datetime = None
        self.set_min_max_datetime()

        self.location_options = None
        self.set_location_options()

        self.gateway_options = None     # formerly known as 'residents'
        self.set_gateway_options()

    
    def set_min_max_datetime(self):
        '''
        Sets obj vars and returns max_datetime and min_datetime found in the database
        '''

         # Get connection, which incidentally closes itself during garbage collection
        factory = connection_manager()
        connection = factory.connection

        query = """SELECT MAX(server_timestamp) as 'max' , 
                          MIN(server_timestamp) as 'min' 
                          FROM {};""".format(table_name)

        # Get cursor
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()

            #set class vars
            self.max_datetime = result['max']
            self.min_datetime = result['min']

            # return
            return result['max'], result['min']


    def set_location_options(self):
        '''
        Sets obj vars and returns list of distinct sensor location options found in the database
        '''

         # Get connection, which incidentally closes itself during garbage collection
        factory = connection_manager()
        connection = factory.connection

        query = """SELECT DISTINCT `sensor_location` AS 'locations' FROM ;""".format(table_name)

        # Get cursor
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()

            locations = []
            for d in result:
                locations.append(d['locations'])

            #set class vars
            self.location_options = locations

            # return
            return locations

    
    def set_gateway_options(self):
        '''
        Sets obj vars and returns list of distinct resident options found in the database
        '''

         # Get connection, which incidentally closes itself during garbage collection
        factory = connection_manager()
        connection = factory.connection

        query = """SELECT DISTINCT `gateway_id` AS 'gateways' FROM ;""".format(table_name)

        # Get cursor
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()

            gateways = []
            for d in result:
                gateways.append(d['gateways'])

            #set class vars
            self.gateway_options = gateways

            # return
            return gateways


    def load_csv(self, folder):
        '''
        This method loads a local csv file to the database, and updates the obj vars: min / max datetime, location_options, gateway_options

        Keyword arguments:
        folder -- path to folder containing csv files
        '''
        
        # Get connection, which incidentally closes itself during garbage collection
        factory = connection_manager()
        connection = factory.connection

        # Aggregate all sensor file paths
        all_file_paths = []
        for file in os.listdir(folder):
            filename = os.fsdecode(file)
            filepath = os.path.join(folder, filename)
            if filename.endswith("-sensor.csv"):
                all_file_paths.append(filepath.replace("\\", "\\\\"))

        load_sql = """LOAD DATA LOCAL INFILE '{}' 
                    INTO TABLE {} 
                    FIELDS TERMINATED BY ',' 
                    ENCLOSED BY '' 
                    IGNORE 1 LINES 
                    (@device_id, @device_loc, @gw_device, @gw_timestamp, @key, @reading_type, @server_timestamp, @value) 
                    SET sensor_id = @device_id, 
                        sensor_location = @device_loc, 
                        gateway_id = CAST(@gw_device AS UNSIGNED), 
                        gateway_timestamp = STR_TO_DATE(@gw_timestamp,'%Y-%m-%dT%H:%i:%s'), 
                        `key` = @key, 
                        reading_type = @reading_type, 
                        server_timestamp = STR_TO_DATE(@server_timestamp,'%Y-%m-%dT%H:%i:%s'), 
                        value =CAST(@value AS UNSIGNED);
                    """

        # Get cursor
        with connection.cursor() as cursor:

            # run queries
            for path in all_file_paths:
                cursor.execute(load_sql.format(path, table_name))
                # you might be wondering here why I dont use batch queries. 
                # Its bcause the library uses %s as place holders, AND SO DOES MYSQL >:(

        # Reset params
        self.set_min_max_datetime()
        self.set_location_options()
        self.set_gateway_options()


    def get_logs(self, sensor_location, start_datetime, end_datetime, gateway_id):
        '''
        Returns a list of logs found in the database according to the parameters given

                query = """
                SELECT * FROM 
                WHERE `sensor_location` = \"{}\"
                AND `gateway_timestamp` > '{}'
                AND `gateway_timestamp` < '{}'
                AND `gateway_id` = {}
                """.format(table_name, sensor_location, start_datetime, end_datetime, gateway_id)

        Keyword arguments:
        sensor_location -- based off self.location_options
        start_datetime  -- datetime obj
        end_datetime    -- datetime obj
        gateway_id      -- based off self.gateway_options
        '''

        query = """
                SELECT * FROM 
                WHERE `sensor_location` = \"{}\"
                AND `gateway_timestamp` > '{}'
                AND `gateway_timestamp` < '{}'
                AND `gateway_id` = {}
                """.format(table_name, sensor_location, start_datetime, end_datetime, gateway_id)
        # Get connection, which incidentally closes itself during garbage collection
        factory = connection_manager()
        connection = factory.connection

         # Get cursor
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()

            logs = []
            for d in result:
                sensor_id         = d[Log.sensor_id_tname]
                sensor_location   = d[Log.sensor_location_tname]
                gateway_id        = d[Log.gateway_id_tname]
                gateway_timestamp = d[Log.gateway_timestamp_tname]
                key               = d[Log.key_tname]
                reading_type      = d[Log.reading_type_tname]
                server_timestamp  = d[Log.server_timestamp_tname]
                value             = d[Log.value_tname]

                row_log_obj = Log(sensor_id=sensor_id, sensor_location=sensor_location, 
                                  gateway_id=gateway_id, gateway_timestamp=gateway_timestamp, 
                                  key=key, reading_type=reading_type, server_timestamp=server_timestamp, 
                                  value=value)
                logs.append(row_log_obj)
            # return
            return logs


    # previously known as get_num_activities_by_date
    def get_activities_per_period(self, sensor_location, start_datetime, 
                                     end_datetime, gateway_id, time_period, 
                                     offset=False, min_secs=3):
        '''
        Returns list of Entities.activity objects extrapolated fom sesnsor_logs found in the database queried according to the params given
        i.e. Activities that can be extrapolated from the sensor log database
        
        Keyword arguments:
        sensor_location -- For a list, see self.sensor_location_options
        start_datetime  -- datetime obj
        end_datetime    -- datetime obj
        gateway_id      -- For a list see self.gateway_id_options
        offset          -- If True, considers the previous dates night period as part of this day. 
        min_secs        -- Ignores activities that are of seconds < min_secs. (default 3)
        '''

        # Get all logs
        logs = self.get_logs(sensor_location=sensor_location, start_datetime=start_datetime, end_datetime=end_datetime, gateway_id=gateway_id)

        # Extrpolate actities
        activities = []
        for i in range(len(logs)):
            if i+1 < len(logs) and logs[i].value == 255:
                activity_obj = Activity(sensor_location=sensor_location, 
                                        start_log=logs[i], 
                                        end_log=logs[i+1], 
                                        gateway_id=gateway_id)
                activities.append(activity_obj)

        # offset option
        if offset:
            previous_day_activities = elf.get_activities(sensor_location=sensor_location, 
                                                        start_datetime=start_datetime - datetime.timedelta(days=1), 
                                                        end_datetime=end_datetime -  + datetime.timedelta(days=1),
                                                        gateway_id=gateway_id)
            previous_night_activities = [activity for activity in previous_day_activities if not activity.in_daytime()]
            activities = activites + previous_night_activities
        
        # Drration filter
        if min_secs > 0:
            activities = [activity for activity in activities if activity.seconds >= min_secs]

        # time period filter
        if time_period == 'Day':
            activites = [activity for activity in activities if activity.in_daytime()]
        elif time_period == 'Night':
            activites = [activity for activity in activities if not activity.in_daytime()]

        return activities
        
        

        

