import datetime, os, sys
from DAOs.connection_manager import connection_manager
import secrets
import string

# from Entities.resident import Resident

table_name = 'stbern.alert_log'

def get_alerts_by_id(chat_id):
    '''
    Returns alert_text and rname by id
    '''
    query = "SELECT alert_text, rname FROM {} WHERE chat_id = %s AND alert_type = %s AND response_status = %s".format(table_name)
    values = (chat_id, "Assistance", "No")
    # chat_id = {} AND 
    # Get connection
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()

    try:
        cursor.execute(query, values)
        results = cursor.fetchall()
        return results
    except: raise
    finally: factory.close_all(cursor=cursor, connection=connection)

def get_latest_alert_by_id(chat_id, rname):
    '''
    Returns alert_text and rname by id
    '''
    query = "SELECT alert_text, response_status FROM {} WHERE chat_id = %s AND alert_type = %s AND date = (select max(date) from {} where rname = %s AND alert_type = %s)".format(table_name, table_name)
    values = (chat_id, "Assistance", rname, "Assistance")
    # chat_id = {} AND 
    # Get connection
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()

    try:
        cursor.execute(query, values)
        results = cursor.fetchall()
        return results
    except: raise
    finally: factory.close_all(cursor=cursor, connection=connection)

def get_sensor_alerts(chat_id, alert_type):
    '''
    Returns sensor alert_text and by id
    '''
    query = "SELECT alert_text FROM {} WHERE chat_id = %s AND alert_type = %s AND response_status = %s".format(table_name)
    values = (chat_id, alert_type, "No")
    # chat_id = {} AND 
    # Get connection
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()

    try:
        cursor.execute(query, values)
        results = cursor.fetchall()
        return results
    except: raise
    finally: factory.close_all(cursor=cursor, connection=connection)


def insert_alert(chat_id, date, rname, alert_text, alert_type, response_status):
    '''
    Returns the id of the inserted resident if successful
    '''
    query = 'INSERT INTO {} (chat_id, date, rname, alert_text, alert_type, response_status) VALUES (%s, %s, %s, %s, %s, %s)'.format(table_name)
    values = (chat_id, date, rname, alert_text, alert_type, response_status)

    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()

    try:
        cursor.execute(query, values)
        return cursor.lastrowid
    except: raise
    finally: factory.close_all(cursor=cursor, connection=connection)

def update_alert(chat_id, alert_text, purpose):
    
    '''
    Update the status of the alert if successful
    '''
    query = "UPDATE {} SET response_status = %s, purpose = %s WHERE chat_id = %s AND alert_text = %s".format(table_name)
    values = ('Yes', purpose, chat_id, alert_text)
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()
    print("alerting")
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

# def main():
    # print(get_alerts_by_id(-251433967))

# if __name__ == '__main__':
    # main()
