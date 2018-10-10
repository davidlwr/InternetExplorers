from flask import render_template, Flask, request, flash, Markup, redirect, url_for
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, RadioField, FloatField, SelectField, IntegerField, HiddenField
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
    dob = db.Column(db.DateTime)
    fall_risk = db.Column(db.String(45))
    status = db.Column(db.String(45))
    stay_location = db.Column(db.String(45))


def resident_query():
    return Resident.query


class ShiftLogForm(Form):
    resident = QuerySelectField(query_factory=resident_query, allow_blank=False, get_label='name')
    date = DateField('Date', format='%Y-%m-%d', validators=[InputRequired('Please enter date!')], default=datetime.today)
    timeNow = datetime.time(datetime.now())
    today7pm = timeNow.replace(hour=19, minute=0, second=0, microsecond=0)
    dayNightSelector = 2
    if timeNow < today7pm:
        dayNightSelector = 1

    time = SelectField('Shift', choices=[(1, 'Day'), (2, 'Night')], coerce=int, default=dayNightSelector)
    falls = IntegerField('Number of Slips/Falls of Resident', default=0)
    near_falls = IntegerField('Number of Near Falls', default=0)
    consumption = SelectField('Food consumption',
                             choices=[(1, 'Insufficient'), (2, 'Moderate'),
                                      (3, 'Excessive')], coerce=int, default=2)
    toilet_visits = HiddenField()
    temperature = FloatField('Temperature (°C) ', default=36.9)
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
            submitted_name = form.resident.data.resident_id
            name_to_show = form.resident.data.name
            submitted_date = form.date.data
            submitted_time = form.time.data
            submitted_falls = form.falls.data
            submitted_near_falls = form.near_falls.data
            submitted_consumption = form.consumption.data
            submitted_toilet_visits = 0
            submitted_temperature = form.temperature.data
            submitted_sbp = form.sbp.data
            submitted_dbp = form.dbp.data
            submitted_pulse = form.pulse.data

            shiftLogDAO = shift_log_DAO()

            if submitted_time == 1:
                day_night = "Day"
            else:
                day_night = "Night"

            shiftLog = Shift_log(submitted_date, submitted_time, submitted_name, submitted_falls, submitted_near_falls,
                                 submitted_consumption, submitted_toilet_visits, submitted_temperature,
                                 submitted_sbp, submitted_dbp, submitted_pulse)

            response = 'Shift log for ' + submitted_date.strftime('%Y-%m-%d') + '(' + day_night + ') for ' + name_to_show + ' has already been recorded. Please enter another date.'
            try:
                shiftLogDAO.insert_shift_log(shiftLog)
            except:
                flash(response)
                return render_template('eosforms.html', form=form)

            response = 'Shift log for ' + name_to_show + ' has been successfully recorded. Click <a href="/admin/shift_log" class="alert-link">here</a> to view/edit responses.'
            flash(Markup(response))
            return redirect(url_for('showForms'))
        else:
            return render_template('eosforms.html', form=form)
    else:
        return render_template('eosforms.html', form=form)

# @server.route("/donewithform")
# def processForms():
#     return
