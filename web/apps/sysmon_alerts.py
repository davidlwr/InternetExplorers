from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, jsonify, current_app
from flask_login import current_user, login_required
from apps import input_data
from app import app, server
from DAOs.connection_manager import connection_manager

table_name = "stbern.alert_log"
chatid_tname = "chat_id"
text_tname   = "alert_text"

LOW_BATT_SUBSTR = "Battery Low"
TYPE_BATT   = 1
TYPE_SENSOR = 2

@server.route('/notifications', methods=['GET', 'POST'])     # see init in main for example
@login_required
def notifications():

    # Get connection
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()

    type_texts = []
    try:
        cursor.execute(f'SELECT * FROM {table_name}')
        result = cursor.fetchone()

        if result != None:      # Append 1. Alert_Type, and 2. Text.        Alert type used to determine icon type
            for r in result:
                alerttext  = r[text_tname]
                alert_type = TYPE_BATT if LOW_BATT_SUBSTR in alerttext else TYPE_SENSOR
                type_texts.append([alert_type, alerttext])
        
    except: raise
    finally: factory.close_all(cursor=cursor, connection=connection)

    return jsonify([{'type': type,
                     'text': text
                    } for type,text in type_texts])

@server.route('/notifications_count', methods=['GET', 'POST'])
@login_required
def notifications_count():
    # Get connection
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()

    try:
        cursor.execute(f'SELECT * FROM {table_name}')
        result = cursor.fetchone()

        if result == None: return 0
        else: len(result)
        
    except: raise
    finally: factory.close_all(cursor=cursor, connection=connection)
