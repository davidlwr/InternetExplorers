import datetime, os, sys
import pandas as pd

if __name__ == '__main__':  sys.path.append("..")
from Entities.sysmon_log import Sysmon_Log
from DAOs.connection_manager import connection_manager

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

    
    def insert_many(self, logs):
        '''
        INSERTs many logs at once

        logs (list) -- [log, log, log]
        '''

        query = f"INSERT INTO {sysmon_log_DAO.table_name} VALUES(%s, %s, %s, %s, %s)"

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        # Batch insert
        try:
            batch = []
            for log in logs:
                uuid    = log.uuid
                node_id = log.node_id
                event   = log.event
                key     = log.key
                ts      = log.recieved_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                l = [uuid, node_id, event, key, ts]
                
                if len(batch) < 500: batch.append(l)    # Batch not full, continue filling
                else:                                   # Batch full, run executemany
                    cursor.executemany(query, batch)
                    batch = []
            
            # Just to clear the last batch if there is anything inside
            if len(batch) > 0: cursor.executemany(query, batch)

        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)
            

    @staticmethod
    def get_all_logs(uuid=None):
        '''
        Returns all sysmon logs in the DB

        Inputs
        uuid (str) -- Filters result by sensor uuid
        '''

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        query = f"SELECT * FROM {sysmon_log_DAO.table_name}"
        if uuid != None: query += f" WHERE `{Sysmon_Log.uuid_tname}` = %s"

        try:
            if uuid == None: cursor.execute(query)
            else: cursor.execute(query, [uuid])
            
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
            # return pd.read_sql_query(query, connection)

        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def get_last_sysmon(uuid, limit=1):
        '''
        Inputs:
        uuid (str) -- ie "2005-m-01"
        limit (int) -- default 1
        '''
        query = f"""SELECT * FROM {sysmon_log_DAO.table_name} 
                    WHERE `{Sysmon_Log.uuid_tname}` = "{uuid}" 
                    ORDER BY `{Sysmon_Log.recieved_timestamp_tname}` 
                    DESC LIMIT {limit}"""
        
        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

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

        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)
        

    @staticmethod
    def get_last_battery_level(uuid, limit=1):
        '''
        Inputs:
        uuid (str) -- ie "2005-m-01"
        limit (int) -- default 1

        Return
        Entity.Sysmon_log
        '''
        query = f"""SELECT * FROM {sysmon_log_DAO.table_name} 
                    WHERE `{Sysmon_Log.uuid_tname}` = "{uuid}" 
                    AND `{Sysmon_Log.key_tname}` = "Battery Level"
                    ORDER BY `{Sysmon_Log.recieved_timestamp_tname}` 
                    DESC LIMIT {limit}"""
        
        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            results = cursor.fetchall()
            if results != None:
                for result in results:
                    uuid    = result[Sysmon_Log.uuid_tname]
                    node_id = result[Sysmon_Log.node_id_tname]
                    event   = result[Sysmon_Log.event_tname]
                    key     = result[Sysmon_Log.key_tname]
                    ts      = result[Sysmon_Log.recieved_timestamp_tname]

                    return Sysmon_Log(uuid, node_id, event, key, ts)
            else: return None

        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)

    
    @staticmethod
    def get_last_burglar(uuid, event=0, limit=1):
        '''
        Inputs:
        uuid (str) -- ie "2005-m-01"
        event (int) -- default 0
        limit (int) -- default 1

        Reutrn
        Entity.Sysmon_log
        '''
        query = f"""SELECT * FROM {sysmon_log_DAO.table_name} 
                    WHERE `{Sysmon_Log.uuid_tname}` = "{uuid}" 
                    AND `{Sysmon_Log.key_tname}` = "Burglar"
                    ORDER BY `{Sysmon_Log.recieved_timestamp_tname}` 
                    DESC LIMIT {limit}"""
        
        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            results = cursor.fetchall()
            if results != None:
                for result in results:
                    uuid    = result[Sysmon_Log.uuid_tname]
                    node_id = result[Sysmon_Log.node_id_tname]
                    event   = result[Sysmon_Log.event_tname]
                    key     = result[Sysmon_Log.key_tname]
                    ts      = result[Sysmon_Log.recieved_timestamp_tname]

                    return Sysmon_Log(uuid, node_id, event, key, ts)
            else: return None

        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)

# TESTS ====================================================================================================
if __name__ == '__main__': 
    # Test 1: get all logs
    print(sysmon_log_DAO.get_all_logs()[-5:])
    print("break")
    print(sysmon_log_DAO.get_all_logs(uuid="2006-m-01")[-5:])
