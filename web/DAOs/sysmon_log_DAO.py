import datetime, os, sys
from connection_manager import connection_manager

if __name__ == '__main__':  sys.path.append("..")
from Entities.sysmon_log import Sysmon_Log


class sysmon_log_DAO(object):
    '''
    This class handles connection between the app and the database table
    '''

    table_name = "stbern.SYSMON_LOG"


    def insert_log(self, log):
        '''
        INSERTs a log entry into the database

        Returns success boolean
        '''

        # Get connection, which incidentally closes itself during garbage collection
        factory = connection_manager()
        connection = factory.connection

        query = "INSERT INTO {} VALUES('{}', '{}', '{}', '{}', '{}')"                        \
                    .format(sysmon_log_DAO.table_name, log.uuid, log.node_id,                \
                            log.event, log.key, log.recieved_timestamp.strftime('%Y-%m-%d %H:%M:%S'))

        with connection.cursor() as cursor:
            try:
                cursor.execute(query)
            except Exception as error:
                print(error)
                raise
            

    def get_all_logs(self):
        '''
        Returns sysmon logs for a uuid between and start and end datetime

        Inputs:
        uuid (str)
        '''

        # Get connection, which incidentally closes itself during garbage collection
        factory = connection_manager()
        connection = factory.connection

        query = f"SELECT * FROM {sysmon_log_DAO.table_name}"

        with connection.cursor() as cursor:
            try:
                cursor.execute(query)
                results = cursor.fetchall()
                logs = []
                if results != None:
                    for result in results:
                        uuid    = result[Sysmon_Log.uuid_tname]
                        node_id = result[Sysmon_Log.node_id_tname]
                        event   = result[Sysmon_Log.event_tname]
                        key     = result[Sysmon_Log.key_tname]
                        ts      = result[Sysmon_Log.recieved_timestamp_tname]

                        log = Sysmon_Log(uuid, node_id, event, key, ts)
                        logs.append(log)
                return logs

            except Exception as error:
                print(error)
                raise
