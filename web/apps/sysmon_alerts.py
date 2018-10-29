from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, jsonify, current_app
from flask_login import current_user, login_required
from app import app, server
from DAOs.connection_manager import connection_manager

LOW_BATT_SUBSTR = "Sensor Issue: Low Battery"
WARNING_SUBSTR  = "Sensor Issue: Warning"
SENSOR_SUBSTR   = "Sensor Issue"
TYPE_BATT   = 1
TYPE_SENSOR = 2


@server.route('/notifications', methods=['GET', 'POST'])     # see init in main for example
def notifications():
    # Get connection
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()

    type_texts = []
    try:
        cursor.execute('SELECT * FROM stbern.alert_log')
        result = cursor.fetchall()
        if result != None:
            for r in result:
                alerttext = r['alert_text']
                datetime  = r['date']
                 
                # Categorize alert types
                if alerttext.startswith(WARNING_SUBSTR):        # Sensor down
                    type_texts.append([TYPE_SENSOR, alerttext[len(SENSOR_SUBSTR):], datetime])
                else:                                           # Low battery
                    type_texts.append([TYPE_BATT, alerttext[len(SENSOR_SUBSTR):], datetime])

    except:     # Fail safely
        return jsonify([{'type': type,
                        'text': text,
                        'date': date
                        } for type,text,date in type_texts])

    finally: factory.close_all(cursor=cursor, connection=connection)

    return jsonify([{'type': type,
                     'text': text,
                     'date': date
                    } for type,text,date in type_texts])


# DONT USE THIS. WRONG. but idk if pat is using this so I didnt remove it.
# NOTE: Fixed the sql statement to take into account response status
@server.route('/notifications_count', methods=['GET', 'POST'])
def notifications_count():
    # Get connection
    factory = connection_manager()
    connection = factory.connection
    cursor = connection.cursor()

    try:
        cursor.execute(f"SELECT * FROM stbern.alert_log WHERE `alert_text` LIKE '{SENSOR_SUBSTR}%' AND `response_status` <> 'Yes'")
        result = cursor.fetchall()

        if result == None: return 0
        else: return len(result)

    except: raise
    finally: factory.close_all(cursor=cursor, connection=connection)
