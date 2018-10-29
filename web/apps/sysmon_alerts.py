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
        cursor.execute(f"SELECT * FROM stbern.alert_log WHERE `alert_text` LIKE '{SENSOR_SUBSTR}%' AND `response_status` <> 'Yes'")
        result = cursor.fetchall()
        if result != None:
            for r in result:
                alerttext = r['alert_text']
                datetime  = r['date']
                 
                # Categorize alert types
                # # Slice text because of lack of standard msg len and theres tabs in here for some reason idk
                if alerttext.startswith(WARNING_SUBSTR):        # Sensor down
                    plain_txt  = alerttext[len(SENSOR_SUBSTR):]     
                    s_header   = plain_txt[0:9]                     
                    s_location = plain_txt[10:(plain_txt.index('Type: ')-1)]
                    s_type     = plain_txt[plain_txt.index('Type: '):]
                    type_texts.append([TYPE_SENSOR, s_header, s_location, s_type, datetime])
                else:                                           # Low battery
                    plain_txt  = alerttext[len(SENSOR_SUBSTR):]
                    s_header   = plain_txt[0:13]
                    s_location = plain_txt[14:(plain_txt.index('Type: ')-1)]
                    s_type     = plain_txt[plain_txt.index('Type: '):]
                    type_texts.append([TYPE_BATT, s_header, s_location, s_type, datetime])

    except:     # Fail safely
        return jsonify([{'type': type,
                        's_header': s_header,
                        's_location': s_location,
                        's_type': s_type,
                        'date': date
                        } for type,s_header,s_location,s_type,date in type_texts])

    finally: factory.close_all(cursor=cursor, connection=connection)

    return jsonify([{'type': type,
                    's_header': s_header,
                    's_location': s_location,
                    's_type': s_type,
                    'date': date
                    } for type,s_header,s_location,s_type,date in type_texts])


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
