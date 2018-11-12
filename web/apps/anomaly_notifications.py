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
        query_text = ''
    except:
        print("Exceptions occurred in anomaly_notifications")
        raise
        # return some empty json to fail safely
    finally:
        factory.close_all(cursor=cursor, connection=connection)