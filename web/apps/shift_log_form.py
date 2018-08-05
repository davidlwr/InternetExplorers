from flask import render_template, Flask, request
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, RadioField, FloatField, SelectField
from wtforms.fields.html5 import DateField
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import InputRequired
import flask_login
from datetime import datetime

from app import app, server, db
from DAOs.shift_log_DAO import shift_log_DAO
from Entities.shift_log import Shift_log


class Resident(db.Model):
    resident_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    node_id = db.Column(db.String(20))
    age = db.Column(db.Integer)
    fall_risk = db.Column(db.String(45))
    status = db.Column(db.String(45))
    stay_location = db.Column(db.String(45))


def resident_query():
    return Resident.query


class ShiftLogForm(Form):
    name = QuerySelectField(query_factory=resident_query, allow_blank=False, get_label='name')
    date = DateField('Date', format='%Y-%m-%d', validators=[InputRequired('Please enter date!')])
    timeNow = datetime.time(datetime.now())
    today7pm = timeNow.replace(hour=19, minute=0, second=0, microsecond=0)
    dayNightSelector = 1
    if timeNow < today7pm:
        dayNightSelector = 1

    time = RadioField('Shift', choices=[(1, 'Day'), (2, 'Night')], coerce=int, default=dayNightSelector)
    falls = RadioField('Number of Slips/Falls of Resident',
                       choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3')], coerce=int)
    near_falls = RadioField('Number of Near Falls',
                            choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3')], coerce=int)
    consumption = RadioField('Food consumption',
                             choices=[('insufficient', 'Insufficient'), ('moderate', 'Moderate'),
                                      ('excessive', 'Excessive')])
    temperature = FloatField('Temperature (°C) ')
    sbp = FloatField('Systolic blood pressure (SBP) mmHg ')
    dbp = FloatField('Diastolic blood pressure (DBP) mmHg ')
    pulse = FloatField('Pulse Rate (b/m)  ')
    submit = SubmitField('Submit')


# settle routing
@server.route("/eosforms", methods=['GET', 'POST'])
@flask_login.login_required
def showForms():
    form = ShiftLogForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            # handle submitted data here
            # process form here
            submitted_name = form.name.data.resident_id
            name_to_show = form.name.data.name
            submitted_date = form.date.data
            submitted_time = form.time.data
            submitted_falls = form.falls.data
            submitted_near_falls = form.near_falls.data
            submitted_consumption = form.consumption.data
            default_value = True
            submitted_toilet_visits = request.form.get('toilet_visits', default_value)
            submitted_temperature = form.temperature.data
            submitted_sbp = form.sbp.data
            submitted_dbp = form.dbp.data
            submitted_pulse = form.pulse.data

            shiftLogDAO = shift_log_DAO()
            shiftLog = Shift_log(submitted_date, submitted_time, submitted_name, submitted_falls, submitted_near_falls,
                                 submitted_consumption, submitted_toilet_visits, submitted_temperature,
                                 submitted_sbp, submitted_dbp, submitted_pulse)
            shiftLogDAO.insert_shift_log(shiftLog)
            return render_template('FormResponse.html', name=name_to_show)
        else:
            return render_template('eosforms.html', form=form)
    else:
        return render_template('eosforms.html', form=form)

# @server.route("/donewithform")
# def processForms():
#     return
