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
        date_in_use = input_data.input_raw_max_date + datetime.timedelta(days=-32) # TODO: change to current system time once live data is available
        r['name'] = resident['name']
        r['node_id'] = resident['node_id']

        # settle night toilet usage
        r['toilet_alerts'], __ = input_data.get_nightly_toilet_indicator(int(resident['node_id']), date_in_use)
        r['toilet_tooltip'] = []
        if len(r['toilet_alerts']) == 0:
            r['toilet_tooltip'].append("Night toilet visit numbers appear normal")
        else: # NOTE: right now we just append, but use separate list for tooltips in case of future changes
            r['toilet_tooltip'].extend(r['toilet_alerts'])

        # settle sleep duration
        r['sleep_alerts'], __, __ = input_data.get_nightly_sleep_indicator(int(resident['node_id']), date_in_use)
        r['sleep_tooltip'] = []
        if len(r['sleep_alerts']) == 0:
            r['sleep_tooltip'].append("Normal level of motion during sleep detected")
        else: # NOTE: for future changes
            r['sleep_tooltip'].extend(r['sleep_alerts'])

        # print("DEBUG resident id sleep_alerts", resident['node_id'], r['sleep_alerts'])
        r['alert_highest'] = max(0, len(r['toilet_alerts']), len(r['sleep_alerts']))
        residents.append(r)
    return render_template('overview_residents.html', residents=residents)

# layer 2 routing
@server.route("/overview/<int:node_id>", methods=['GET', 'POST'])
@flask_login.login_required
def detailedLayerTwoOverviewResidents(node_id):
    date_in_use = input_data.input_raw_max_date + datetime.timedelta(days=-32) # TODO: change to current system time once live data is available
    resident = resident_DAO.get_resident_by_id(node_id)
    if resident is None:
        return 'Resident not found<a href="/overview">Go Back</a>'

    # sleep alerts
    resident['sleep_alerts'], resident['average_motion_during_sleep'], resident['average_motion_during_sleep_difference'] = input_data.get_nightly_sleep_indicator(node_id, date_in_use)

    # toilet alerts
    resident['toilet_alerts'], resident['number_of_night_toilet_usage_in_past_week'] = input_data.get_nightly_toilet_indicator(node_id, date_in_use)
    resident['toilet_night_to_both_ratio'], resident['toilet_night_to_both_std'] = input_data.get_percentage_of_night_toilet_usage(node_id, date_in_use)

    # set indicators  {# NOTE: change identifying text below, if input_data function changes #}
    resident['check_indicator_night_toilet_ratio'] = any('of total daily usage in the past month' in s for s in resident['toilet_alerts'])
    resident['check_indicator_night_toilet_MA'] = any('number of night toilet usage in the last week' in s for s in resident['toilet_alerts'])
    resident['check_indicator_sleep_movements'] = any('movements during sleeping hours' in s for s in resident['sleep_alerts'])
    # get required information here and pass to the template
    return render_template('overview_layer_two.html', resident=resident)
