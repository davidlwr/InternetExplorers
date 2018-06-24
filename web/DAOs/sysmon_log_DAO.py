
class sysmon_log_DAO(object):

    def load_csv(self, folder):
        '''
        This method loads a local csv file to the database

        :param csv_file:    path to folder containing csv files
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


        load_sql = """LOAD DATA LOCAL INFILE '{}' 
                    INTO TABLE stbern.SYSMON_LOG 
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
	                    value = IF(@value LIKE 'None', Null, CAST(@value AS DECIMAL(12,2)));
                    """

        # Get cursor
        with connection.cursor() as cursor:
            # run queries
            for path in all_file_paths:
                cursor.execute(load_sql.format(path))
                # you might be wondering here why I dont use batch queries. 
                # Its bcause the library uses %s as place holders, AND SO DOES MYSQL >:(


