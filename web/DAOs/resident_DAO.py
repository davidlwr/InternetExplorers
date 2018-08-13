import datetime, os, sys
from DAOs.connection_manager import connection_manager
import secrets
import string

from Entities.resident import Resident

table_name = 'stbern.RESIDENT'

def get_resident_by_id(node_id):
    '''
    Returns a resident (in a dict) based on node_id (in int)
    '''
    query = 'SELECT * FROM {} WHERE node_id = %s'.format(table_name)
    factory = connection_manager()
    connection = factory.connection

    with connection.cursor() as cursor:
        cursor.execute(query, (node_id, ))
        result = cursor.fetchone()

        return result

    return None

def get_list_of_residents(filter_active=True, location_filter=None):
    '''
    Returns list of residents (each resident is a dictionary)
    NOTE: returned node_id is in string
    Default selects only active residents
    '''
    query = 'SELECT * FROM {}'.format(table_name)
    if filter_active:
        query += " WHERE status = 'Active'"

    # if location_filter:
        # TODO:
        # NOTE: not implemented yet
        # pass
        # query +=

    factory = connection_manager()
    connection = factory.connection
    # print(query)
    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()
        # have to try printing this
        if results:
            # print(results)
            return results
        else:
            return None
    return None

def insert_resident(name, node_id, age, fall_risk=None, status="Active", stay_location="STB"):
    '''
    Returns the id of the inserted resident if successful
    '''
    query = 'INSERT INTO {} (name, node_id, age, fall_risk, status, stay_location) VALUES (%s, %s, %s, %s, %s, %s)'.format(table_name)
    values = (name, node_id, age, fall_risk, status, stay_location)
    factory    = connection_manager()
    connection = factory.connection

    with connection.cursor() as cursor:
        try:
            cursor.execute(query, values)
            return cursor.lastrowid
        except Exception as error:
            print(error)
            raise

def get_resident_name_by_node_id(node_id):
    '''
    Returns the name of the resident based on current node_id
    '''
    resident = get_resident_by_id(node_id)
    if resident is None:
        return None

    return resident['name']
