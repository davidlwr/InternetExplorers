from flask import render_template, Flask, request, url_for
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, RadioField, FloatField
from wtforms.fields.html5 import DateField
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import InputRequired
import flask_login
import datetime
# internal imports
from apps import input_data
from app import app, server
from DAOs import resident_DAO
from Entities import resident

# settle routing
@server.route("/overview", methods=['GET', 'POST'])
@flask_login.login_required
def showOverviewResidents():
    '''
    This method prepares all the necessary variables to pass into the html for display
    Each resident will have the following:
    Name ('name'), List of Toilet Alerts ('toilet_alerts'),
            List of Sleep Alerts (WIP), Overall Alert Level ('alert_highest')
    NOTE: jinja templates do not allow for import of python modules, so all calculation will be done here
    '''
    residents_raw = resident_DAO.get_list_of_residents()
    residents = []
    for resident in residents_raw:
        r = {}
        r['name'] = resident['name']
        r['toilet_alerts'] = input_data.get_nightly_toilet_indicator(int(resident['node_id']), input_data.input_raw_max_date + datetime.timedelta(days=-30)) # TODO: change to current system time once live data is available
        r['alert_highest'] = max(0, len(r['toilet_alerts']))
        residents.append(r)
    return render_template('overview_residents.html', residents=residents)
