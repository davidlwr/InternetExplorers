from flask import render_template, Flask, request, url_for
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, RadioField, FloatField
from wtforms.fields.html5 import DateField
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import InputRequired
import flask_login
import datetime
import plotly
import json
import pandas as pd
import sys

# internal imports
if __name__ == '__main__':
    sys.path.append(".")
    import input_data
    from app import app, server
    from DAOs import resident_DAO, sensor_hist_DAO
    from sensor_mgmt import sensor_mgmt, JuvoAPI
    from DAOs.sensor_DAO import sensor_DAO
    from Entities import resident
else:
    from apps import input_data
    from app import app, server
    from DAOs import resident_DAO, sensor_hist_DAO
    from sensor_mgmt import sensor_mgmt, JuvoAPI
    from DAOs.sensor_DAO import sensor_DAO
    from Entities import resident

# settle routing
@server.route("/sensor_mgmt", methods=['GET', 'POST'])
@flask_login.login_required
def showOverviewSensors():
    '''
    This method prepares all the necessary variables to pass into the html for display
    Each resident will have the following:
    Name ('name'), List of Toilet Alerts ('toilet_alerts'),
            List of Sleep Alerts (WIP), Overall Alert Level ('alert_highest')
    NOTE: jinja templates do not allow for import of python modules, so all calculation will be done here
    '''
    
    
    residents_raw = resident_DAO.get_list_of_residents()
    
    

    residents = []
    date_in_use = datetime.datetime.now() # datetime.datetime(2018, 4, 19, 23, 34, 12) # TODO: change to current system time once live data is available
    juvo_date_in_use = datetime.datetime.now() # datetime.datetime(2018, 8, 12, 22, 34, 12) # TODO: change to current system time once live data is available
    for resident in residents_raw:
        r = {}
        r['name'] = resident['name']
        r['node_id'] = resident['node_id']
        residentid = resident_DAO.get_resident_id_by_resident_name(resident['name'])
        uuids = sensor_hist_DAO.get_uuids_by_id(residentid['resident_id']) #listofuuids
        
        infoList = []
        for uuid in uuids:
            
            id = uuid['uuid']
            loc = sensor_DAO.get_location_by_node_id(id)
            location = loc[0]['location']
            info = (id,location)
            infoList.append(info)
        r['infoList'] = infoList
        residents.append(r)
    return render_template('sensor_mgmt.html', residents = residents)


if __name__ == '__main__':
    showOverviewSensors()
    pass
