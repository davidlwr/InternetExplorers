from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, jsonify, current_app
import flask_login
from flask_login import current_user, login_required
from app import app, server
from DAOs.connection_manager import connection_manager

@server.route('/anomaly_notifications', methods=['GET', 'POST'])
@flask_login.login_required
def anomaly_notifications():
    # need check whether need start date and end dates or not
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()
    
    try:
        # query_text = 'SELECT * FROM stbern.anomaly WHERE response = 0'
        query_text = 'SELECT resident.resident_id, name, date, category, type, description, response FROM stbern.anomaly LEFT JOIN resident on resident.resident_id = anomaly.resident_id WHERE response = 0'
        cursor.execute(query_text)
        result = cursor.fetchall()
        if result != None:
            return jsonify(result)
        else:
            return ''
    except:
        print("Exceptions occurred in anomaly_notifications")
        # raise
        # return some empty json to fail safely
        return jsonify()
    finally:
        factory.close_all(cursor=cursor, connection=connection)
        
    return jsonify(result)

@server.route('/anomaly_notifications_count', methods=['GET', 'POST'])
@flask_login.login_required
def anomaly_notifications_count():
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()
    
    try:
        query_text = 'SELECT * FROM stbern.anomaly WHERE response = 0'
        cursor.execute(query_text)
        result = cursor.fetchall()
        if result != None:
            return str(len(result))
        else:
            return ''
    except:
        print("Exceptions occurred in anomaly_notifications_count")
        # raise
        # return some number to fail safely
        return str(-1)
    finally:
        factory.close_all(cursor=cursor, connection=connection)
        
    return str(len(result))
    
@server.route('/anomaly_notifications_read', methods=['POST'])
@flask_login.login_required
def mark_anomaly_read():
    input_msg = request.get_json()
    # print(str(input_msg))
    
    # update the database to mark as read
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()
    
    try:
        # maybe validate the parameters in the JSON here first
        query_text = 'UPDATE stbern.anomaly SET `response` = 1 WHERE date = %s and resident_id = %s and type = %s and description = %s'
        values = (input_msg['date'], input_msg['resident_id'], input_msg['type'], input_msg['desc_text']) # need double check table column names and json keys
        
        cursor.execute(query_text, values)
        connection.commit()
    except:
        print("Exceptions occurred at anomaly_notifications_read")
        raise
    
    finally:
        factory.close_all(cursor=cursor, connection=connection)
    
    return str(input_msg)