from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, jsonify, current_app
from flask_login import current_user, login_required
from app import app, server
from DAOs.connection_manager import connection_manager

@server.route('/anomaly_notifications', methods=['GET', 'POST'])
def anomaly_notifications():
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()
    
    try:
        query_text = 'SELECT * FROM stbern.anomaly WHERE response = 0'
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
        print("Exceptions occurred in anomaly_notifications")
        # raise
        # return some number to fail safely
        return str(-1)
    finally:
        factory.close_all(cursor=cursor, connection=connection)
        
    return str(len(result))