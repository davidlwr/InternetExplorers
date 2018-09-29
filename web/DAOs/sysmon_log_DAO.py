import datetime, os, sys
import pandas as pd

if __name__ == '__main__':  sys.path.append("..")
from Entities.sysmon_log import Sysmon_Log
from DAOs.connection_manager import connection_manager

class sysmon_log_DAO(object):
    '''
    This class handles connection between the app and the database table
    '''

    table_name = "stbern.sysmon_log"


    def insert_log(self, log):
        '''
        INSERTs a log entry into the database

        Returns success boolean
        '''
        query = "INSERT INTO {} VALUES('{}', '{}', '{}', '{}', '{}')"                        \
                    .format(sysmon_log_DAO.table_name, log.uuid, log.node_id,                \
                            log.event, log.key, log.recieved_timestamp.strftime('%Y-%m-%d %H:%M:%S'))

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def get_all_logs():
        '''
        Returns all sysmon logs in the DB
        '''

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        # cursor = connection.cursor()

        query = f"SELECT * FROM {sysmon_log_DAO.table_name}"

        try:
            # cursor.execute(query)
            # results = cursor.fetchall()
            # logs = []
            # if results != None:
            #     for result in results:
            #         uuid    = result[Sysmon_Log.uuid_tname]
            #         node_id = result[Sysmon_Log.node_id_tname]
            #         event   = result[Sysmon_Log.event_tname]
            #         key     = result[Sysmon_Log.key_tname]
            #         ts      = result[Sysmon_Log.recieved_timestamp_tname]
            #
            #         log = Sysmon_Log(uuid, node_id, event, key, ts)
            #         logs.append(log)
            # return logs
            return pd.read_sql_query(query, connection)

        except: raise
        # finally: factory.close_all(cursor=cursor, connection=connection)
        finally: factory.close_all(connection=connection)
