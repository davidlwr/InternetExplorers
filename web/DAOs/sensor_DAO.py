import datetime, os, sys
import pandas as pd

if __name__ == '__main__':  sys.path.append("..")
from DAOs.connection_manager import connection_manager
from Entities.sensor_log import Sensor_Log
from Entities.activity import Activity


table_name = 'stbern.sensor'

def get_location_by_node_id(node_id):
    '''
    Returns a resident (in a dict) based on node_id (in int)
    '''
    query = 'SELECT location FROM {} WHERE uuid = %s'.format(table_name)
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