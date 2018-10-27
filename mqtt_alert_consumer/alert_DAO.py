import datetime, os, sys
from connection_manager import connection_manager
import secrets
import string

# from Entities.resident import Resident

table_name = 'stbern.alert_log'

def get_alerts_by_id(chat_id):
    '''
    Returns a resident (in a dict) based on node_id (in int)
    '''
    query = 'SELECT alert_text FROM {} WHERE chat_id = {} AND reponse_status = {}'.format(table_name, chat_id, "No")
    # Get connection
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()

    try:
        cursor.execute(query)
        results = cursor.fetchall()
        print(len(results))
        return results
    except: raise
    finally: factory.close_all(cursor=cursor, connection=connection)


def insert_alert(chat_id, date, alert_text, alert_type, response_status):
    '''
    Returns the id of the inserted resident if successful
    '''
    query = 'INSERT INTO {} (chat_id, date, alert_text, alert_type, response_status) VALUES (%s, %s, %s, %s, %s)'.format(table_name)
    values = (chat_id, alert_text)

    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()

    try:
        cursor.execute(query, values)
        return cursor.lastrowid
    except: raise
    finally: factory.close_all(cursor=cursor, connection=connection)

def update_alert(chat_id, alert_text):
    '''
    Returns the id of the inserted resident if successful
    '''
    query = 'UPDATE {} SET Response_status = {} WHERE chat_id = {} AND alert_text = {}'.format(table_name, "Yes", chat_id, alert_text)
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()

    try:
        cursor.execute(query, values)
        return cursor.lastrowid
    except: raise
    finally: factory.close_all(cursor=cursor, connection=connection)    

def delete_alert(chat_id, alert_text):
    '''
    Returns the name of the resident based on current node_id
    '''
    query = 'DELETE FROM {} WHERE CHAT_ID = {} AND alert_text = {}'.format(table_name, chat_id, alert_text)

    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()

    try:
        cursor.execute(query)
        return cursor.lastrowid
    except: raise
    finally: factory.close_all(cursor=cursor, connection=connection)
