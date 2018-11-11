import datetime, os, sys
from DAOs.connection_manager import connection_manager
import string


table_name = 'stbern.anomaly'

def get_list_of_anomalies(startDate, endDate):
    '''
    Returns list of anomalies (each anomaly is a dictionary)
    '''
    query = 'SELECT * FROM {} where date >= %s and date <= %s order by date'.format(table_name)
    
    values = (startDate, endDate)
    # Get connection
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()

    try:
        cursor.execute(query, values)
        results = cursor.fetchall()
        # have to try printing this
        return results
    except:
        raise
    finally:
        factory.close_all(cursor=cursor, connection=connection)


def insert_anomaly(date, resident_id, category, type, description, response):
    '''
    Returns the id of the inserted resident if successful
    '''

    query = 'INSERT INTO {} (date, resident_id, category, type, description, response) VALUES (%s, %s, %s, %s, %s, %s)'.format(table_name)
    values = (date, resident_id, category, type, description, response)

    # Get connection
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()

    try:
        cursor.execute(query, values)
        return cursor.lastrowid
    except:
        raise
    finally:
        factory.close_all(cursor=cursor, connection=connection)


def update_anomaly(date, resident_id, category, type, description):
    '''
    Returns a resident (in a dict) based on resident_id (in int)
    '''
    query = 'UPDATE {} SET `response` = %s WHERE date = %s and resident_id = %s and category = %s and type = %s and description = %s'.format(table_name)
    val = (1, date, resident_id, category, type, description)
    # Get connection
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()

    try:
        cursor.execute(query, val)
        connection.commit()
    except:
        raise
    finally:
        factory.close_all(cursor=cursor, connection=connection)

# if __name__ == '__main__':
    # insert_anomaly('2018-10-30', 1, "vitals", "bp", "high", 0)


