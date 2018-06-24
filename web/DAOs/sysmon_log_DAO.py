
class sysmon_log_DAO(object):
    '''
    This class handles connection between the app and the database table
    '''

    table_name = "stbern.SYSMON_LOG"

    def load_csv(self, folder):
        '''
        This method loads a local csv file to the database

        Keyword arguments:
        csv_file -- Path to folder containing csv files
        '''

        # Get connection, which incidentally closes itself during garbage collection
        factory = connection_manager()
        connection = factory.connection

        # Aggregate all sysmon file paths
        all_file_paths = []
        for file in os.listdir(folder):
            filename = os.fsdecode(file)
            filepath = os.path.join(folder, filename)

            if filename.edswith("-sysmon.csv"): 
                all_file_paths.append(filepath.replace("\\", "\\\\"))

        # Get cursor
        with connection.cursor() as cursor:
            # run queries
            for path in all_file_paths:
                
                load_sql = """LOAD DATA LOCAL INFILE '{}' 
                            INTO TABLE {} 
                            FIELDS TERMINATED BY ',' 
                            ENCLOSED BY '' 
                            IGNORE 1 LINES 
                            (@device_id, @device_loc, @gw_device, @gw_timestamp, @key, @reading_type, @server_timestamp, @value) 
                            SET `{}` = IF(@device_id    = '', NULL, @device_id), 
                                `{}` = IF(@device_loc   = '', NULL, @device_loc), 
                                `{}` = IF(@gw_device    = '', NULL, CAST(@gw_device AS UNSIGNED)), 
                                `{}` = IF(@gw_timestamp = '', NULL, STR_TO_DATE(@gw_timestamp,'%Y-%m-%dT%H:%i:%s')), 
                                `{}` = IF(@key          = '', NULL, @key), 
                                `{}` = IF(@reading_type = ''. NULL, @reading_type), 
                                `{}` = IF(@server_timestamp = ''. NULL, STR_TO_DATE(@server_timestamp,'%Y-%m-%dT%H:%i:%s')), 
                                `{}` = IF(@value        = '', NULL, CAST(@value AS DECIMAL(12,2)));
                            """.format(path, 
                                        table_name, 
                                        Log.sensor_id_tname,
                                        Log.sensor_location_tname,
                                        Log.gateway_id_tname,
                                        Log.gateway_timestamp_tname,
                                        Log.key_tname,
                                        Log.server_timestamp_tname,
                                        Log.value_tname)

                cursor.execute(load_sql)



