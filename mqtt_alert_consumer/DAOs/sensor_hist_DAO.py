import datetime, os, sys
import pandas as pd

if __name__ == '__main__':  sys.path.append("..")
from DAOs.connection_manager import connection_manager
from Entities.sensor_log import Sensor_Log
from Entities.activity import Activity


table_name = 'stbern.sensor_ownership_hist'

def get_uuids_by_id(id):
    '''
    Returns a resident (in a dict) based on node_id (in int)
    '''
    query = 'SELECT uuid FROM {} WHERE resident_id = %s'.format(table_name)
    # Get connection
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()

    try:
        cursor.execute(query, (id, ))
        results = cursor.fetchall()
        if results: return results
        else: return []
    except: raise
    finally: factory.close_all(cursor=cursor, connection=connection)


def get_id_by_uuid(uuid):
    '''
    Returns a resident (in a dict) based on node_id (in int)
    '''
    query = 'SELECT distinct(resident_id) FROM {} WHERE uuid = %s'.format(table_name)
    # Get connection
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()

    try:
        cursor.execute(query, (uuid, ))
        results = cursor.fetchall()
        if results: return results
        else: return []
    except: raise
    finally: factory.close_all(cursor=cursor, connection=connection)