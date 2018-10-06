import datetime, os, sys
import pandas as pd

if __name__ == '__main__':  sys.path.append("..")
from DAOs.connection_manager import connection_manager
from Entities.sensor_log import Sensor_Log
from Entities.activity import Activity


class sensor_log_DAO(object):
    """
    This class handles the connection between the app and the datebase table
    """

    table_name = "stbern.sensor_log"
    TIMEPERIOD_DAY   = 'Day'
    TIMEPERIOD_NIGHT = 'Night'

    def __init__(self):
        """
        initialize by setting descriptive vars
        """
        self.max_datetime = None
        self.min_datetime = None
        self.set_min_max_datetime

    @property
    def set_min_max_datetime(self):
        """
        Sets obj vars and returns max_datetime and min_datetime found in the database

        Returns:
        (max_datetime, min_datetime) or (None, None) if nothing found
        """

        query = """SELECT MAX({}) as 'max' , 
                          MIN({}) as 'min' 
                          FROM {};""" \
            .format(Sensor_Log.recieved_timestamp_tname, \
                    Sensor_Log.recieved_timestamp_tname, \
                    sensor_log_DAO.table_name)

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            result = cursor.fetchone()

            # set class vars
            if result != None:
                self.max_datetime = result['max']
                self.min_datetime = result['min']
                return result['max'], result['min']
            else: return None, None

        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def insert_sensor_log(sensor_log):
        """
        INSERTs a log entry into the database

        Inputs:
        sensor_log (Entities.shift_log)
        """

        query = "INSERT INTO {} VALUES(%s, %s, %s, %s)" \
            .format(sensor_log_DAO.table_name)

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, sensor_log.var_list)
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def get_logs(uuid, start_datetime, end_datetime):
        """
        Returns a list of logs found in the database according to the parameters given

        Inputs:
        uuid (str) -- Sensor identifier
        start_datetime (datetime)
        end_datetime (datetime)
        """

        query = """
                SELECT * FROM {}
                WHERE '{}' = %s
                AND `{}` > %s
                AND `{}` < %s
                ORDER BY `{}`
                DESC
                """.format(sensor_log_DAO.table_name, Sensor_Log.uuid_tname, Sensor_Log.recieved_timestamp_tname,
                           Sensor_Log.recieved_timestamp_tname, Sensor_Log.recieved_timestamp_tname)

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, [uuid, start_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                                   end_datetime.strftime('%Y-%m-%d %H:%M:%S')])
            result = cursor.fetchall()

            logs = []
            if result != None:
                for d in result:
                    uuid = d[Sensor_Log.uuid_tname]
                    node_id = d[Sensor_Log.node_id_tname]
                    event = d[Sensor_Log.event_tname]
                    recieved_timestamp = d[Sensor_Log.recieved_timestamp_tname]

                    row_log_obj = Sensor_Log(uuid=uuid, node_id=node_id, event=event,
                                             recieved_timestamp=recieved_timestamp)
                    logs.append(row_log_obj)
            return logs

        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def get_activities_per_period(uuid, start_datetime, end_datetime, time_period=None, min_secs=3):
        """
        Returns list of Entities.activity objects extrapolated fom sesnsor_logs found in the database queried according to the params given
        i.e. Activities that can be extrapolated from the sensor log database

        Keyword arguments:
        uuid (str)           -- sensor identifier
        start_datetime (datetime)  -- datetime obj
        end_datetime  (datetime)   -- datetime obj
        timeperiod (str)      -- 'Day' or 'Night'
        min_secs (int)        -- Ignores activities that are of seconds < min_secs. (default 3)
        """

        # Get all logs
        logs = sensor_log_DAO.get_logs(uuid=uuid, start_datetime=start_datetime, end_datetime=end_datetime)

        # Extrpolate actities
        activities = []
        for i in range(len(logs)):
            if i + 1 < len(logs) and logs[i].value == 255:
                activity_obj = Activity(uuid=uuid,
                                        start_log=logs[i],
                                        end_log=logs[i + 1])
                activities.append(activity_obj)

        # Drration filter
        if min_secs > 0:
            activities = [activity for activity in activities if activity.seconds >= min_secs]

        # time period filter
        if time_period == 'Day':
            activities = [activity for activity in activities if activity.in_daytime()]
        elif time_period == 'Night':
            activities = [activity for activity in activities if not activity.in_daytime()]

        return activities


    @staticmethod
    def get_all_logs():
        """
        Returns all logs in a dataframe
        """

        query = "SELECT * FROM {}".format(sensor_log_DAO.table_name)

        # Get connection
        factory = connection_manager()
        connection = factory.connection

        return pd.read_sql_query(query, connection)

    @staticmethod
    def get_enclosing_logs(start_dt, end_dt, target_dt):
        '''
        Given a target datetime, returns...
        Last record before the target and first record after the target 
        
        Inputs:
        start_dt  (datetime)
        end_dt    (datetime)
        target_dt (datetime)

        Returns:
        records as returned by pymysql
        NOTE: Can have 0, 1, or 2 records. Sorted in ascending datetime
        '''
        feed_dict = [target_dt, start_dt, end_dt, target_dt, start_dt, end_dt]
        query = f"""SELECT * FROM 
                        (SELECT * FROM {sensor_log_DAO.table_name} 
                        WHERE {Sensor_Log.recieved_timestamp_tname} < %s
                        AND {Sensor_Log.recieved_timestamp_tname} > %s
                        AND {Sensor_Log.recieved_timestamp_tname} < %s
                        ORDER BY {Sensor_Log.recieved_timestamp_tname} ASC
                        LIMIT 1) as a
                        union
                        (SELECT * FROM {sensor_log_DAO.table_name} 
                        WHERE {Sensor_Log.recieved_timestamp_tname} > %s
                        AND {Sensor_Log.recieved_timestamp_tname} > %s
                        AND {Sensor_Log.recieved_timestamp_tname} < %s
                        ORDER BY {Sensor_Log.recieved_timestamp_tname} DESC
                        LIMIT 1)
                    ORDER BY {Sensor_Log.recieved_timestamp_tname} ASC
                """
        
        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, feed_dict)
            result = cursor.fetchall()

            enclosing_logs = [None, None]
            if result != None: 
                for r in result:
                    r_ts = r[Sensor_Log.recieved_timestamp_tname]
                    if r_ts < target_dt: enclosing_logs[0] = r_ts
                    else: enclosing_logs[1] = r_ts
            return enclosing_logs
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def get_last_logs(uuid, limit=1):
        """
        Returns a list of logs found in the database according to the parameters given

        Inputs:
        uuid (str) -- Sensor identifier
        limit (int) -- default=1
        """

        query = f"""
                SELECT * FROM {sensor_log_DAO.table_name}
                WHERE {Sensor_Log.uuid_tname} = "{uuid}"
                ORDER BY `{Sensor_Log.recieved_timestamp_tname}` 
                DESC LIMIT {limit}
                """

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            result = cursor.fetchall()

            logs = []
            if result != None:
                for d in result:
                    uuid               = d[Sensor_Log.uuid_tname]
                    node_id            = d[Sensor_Log.node_id_tname]
                    event              = d[Sensor_Log.event_tname]
                    recieved_timestamp = d[Sensor_Log.recieved_timestamp_tname]

                    row_log_obj = Sensor_Log(uuid=uuid, node_id=node_id, event=event, recieved_timestamp=recieved_timestamp)
                    logs.append(row_log_obj)
            return logs

        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def get_all_uuids():
        """
        Returns all distinct sensor UUIDs found in the table

        Returns
        list of str: ["uuid1",... "uuid10"]
        """
        query = f"SELECT DISTINCT(`uuid`) FROM {sensor_log_DAO.table_name}"

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            result = cursor.fetchall()

            uuids = []
            if result != None:
                for r in result:
                    uuids.append(r[Sensor_Log.uuid_tname])
            return uuids

        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)
            

# TESTS ======================================================================================
if __name__ == '__main__': 
    print(sensor_log_DAO.get_all_uuids())
