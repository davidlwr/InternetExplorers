from flask import render_template, Flask, request
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, RadioField, FloatField
from wtforms.fields.html5 import DateField
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import InputRequired
import flask_login

from app import app, server, db
from DAOs.shift_log_DAO import shift_log_DAO
from Entities.shift_log import Shift_log


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45))
    age = db.Column(db.Integer)
    fall_risk = db.Column(db.String(45))
    status = db.Column(db.String(45))


def patient_query():
    return Patient.query


class SampleForm(Form):
    name = QuerySelectField(query_factory=patient_query, allow_blank=True, get_label='name')
    date = DateField('Date', format='%Y-%m-%d', validators=[InputRequired('Please enter date!')])
    falls = RadioField('Number of Slips/Falls of Resident',
                       choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3')], coerce=int)
    near_falls = RadioField('Number of Near Falls',
                            choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3')], coerce=int)
    consumption = RadioField('Food consumption',
                             choices=[('insufficient', 'Insufficient'), ('moderate', 'Moderate'),
                                      ('excessive', 'Excessive')])
    temperature = FloatField('Temperature (°C) taken at 3PM (leave blank if temperature has been taken')
    bp = FloatField('Weekly Blood Pressure Reading (Update only on every Sunday)')
    submit = SubmitField('Submit')


# settle routing
@server.route("/eosforms", methods=['GET', 'POST'])
@flask_login.login_required
def showForms():
    form = SampleForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            # handle submitted data here
            # process form here
            submitted_name = form.name.data.id
            submitted_date = form.date.data
            submitted_falls = form.falls.data
            submitted_near_falls = form.near_falls.data
            submitted_consumption = form.consumption.data
            default_value = True
            submitted_toilet_visits = request.form.get('toilet_visits', default_value)
            submitted_temperature = form.temperature.data
            submitted_bp = form.bp.data

            shiftLogDAO = shift_log_DAO()
            shiftLog = Shift_log(submitted_date, submitted_name, submitted_falls, submitted_near_falls,
                                 submitted_consumption, submitted_toilet_visits, submitted_temperature,
                                 submitted_bp)
            shiftLogDAO.insert_shift_log(shiftLog)
            return render_template('sample.html', name=submitted_name, date=submitted_date, falls=submitted_falls,
                                   near_falls=submitted_near_falls, consumption=submitted_consumption,
                                   toilet_visits=submitted_toilet_visits, temperature=submitted_temperature,
                                   bp=submitted_bp)
        else:
            return render_template('eosforms.html', form=form)
    else:
        return render_template('eosforms.html', form=form)

# @server.route("/donewithform")
# def processForms():
#     return
