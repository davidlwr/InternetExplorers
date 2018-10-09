from flask import render_template, Flask, request, flash, Markup, redirect, url_for
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, RadioField, FloatField, SelectField, IntegerField, HiddenField
from wtforms.fields.html5 import DateField
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import InputRequired
import flask_login
from DAOs.sensor_DAO import sensor_DAO
from datetime import datetime, date

from app import app, server, db
from apps.shift_log_form import resident_query
from sensor_mgmt.JuvoAPI import JuvoAPI
from Entities.sensor import Sensor


class Facility(db.Model):
    abrv = db.Column(db.String(45), primary_key=True)
    fullname = db.Column(db.String(45))
    description = db.Column(db.String(45))


def facility_query():
    return Facility.query


class SensorCreateForm(Form):
    # uuid = StringField('uuid', validators=[InputRequired()])
    uuid = SelectField('UUID')
    type = SelectField('Type', choices=[('door', 'door'), ('motion', 'motion')], validators=[InputRequired()])
    facility = QuerySelectField(query_factory=facility_query, allow_blank=False, get_label='fullname')
    location = SelectField('location', choices=[('bedroom', 'bedroom'), ('toilet', 'toilet')],
                           validators=[InputRequired()])
    description = StringField('Description')
    resident = QuerySelectField(query_factory=resident_query, allow_blank=False, get_label='name')
    # juvo_target = IntegerField('juvo target', validators=[InputRequired()])
    # facility_abrv = StringField('facility abbreviation', validators=[InputRequired()])
    submit = SubmitField('Submit')


class BedSensorCreateForm(Form):
    juvo_id = SelectField('UUID', coerce=int)
    facility = QuerySelectField(query_factory=facility_query, allow_blank=False, get_label='fullname')
    description = StringField('Description')
    resident = QuerySelectField(query_factory=resident_query, allow_blank=False, get_label='name')


previous = 0


@server.route("/createsensorform", methods=['GET', 'POST'])
@flask_login.login_required
def create_sensor():
    global previous
    form = SensorCreateForm()
    uuid_list = sensor_DAO.get_unregistered_uuids()
    form.uuid.choices = [(uuid, uuid) for uuid in uuid_list]
    if len(uuid_list) == 0:
        list1 = "0"
    else:
        list1 = "1"

    form2 = BedSensorCreateForm()
    juvo_id_list = JuvoAPI.get_unregistered_sensors()
    print(juvo_id_list)
    form2.juvo_id.choices = [(juvo_id, juvo_id) for juvo_id in juvo_id_list]
    if len(juvo_id_list) == 0:
        list2 = "0"
    else:
        list2 = "1"

    if request.method == 'POST':
        if form.validate_on_submit():
            # handle logic here
            submitted_uuid = form.uuid.data
            submitted_type = form.type.data
            submitted_facility = form.facility.data.abrv
            submitted_location = form.location.data
            submitted_description = form.description.data
            submitted_resident = form.resident.data.resident_id
            submitted_name = form.resident.data.name

            sensor = Sensor(submitted_uuid, submitted_type, submitted_location, submitted_facility, submitted_description)
            sensor_DAO.insert_sensor(sensor)
            sensor_DAO.insert_ownership_hist(submitted_uuid, submitted_resident, date.today())
            response = 'You have successfully added the ' + submitted_type + ' sensor "' + submitted_uuid + '" for ' + submitted_name + '. Click <a href="/admin/sensor" class="alert-link">here</a> to view/edit responses.'
            flash(Markup(response))
            previous = 0
            return redirect(url_for('create_sensor'))

        if form2.validate_on_submit():
            submitted_juvo_id = form2.juvo_id.data
            submitted_facility = form2.facility.data.abrv
            submitted_description = form2.description.data
            submitted_resident = form2.resident.data.resident_id
            submitted_name = form.resident.data.name

            sensor = Sensor(str(submitted_juvo_id), "bed sensor", "bed", submitted_facility, submitted_description, submitted_juvo_id)
            sensor_DAO.insert_sensor(sensor)
            sensor_DAO.insert_ownership_hist(submitted_juvo_id, submitted_resident, date.today())
            response = 'You have successfully added the bed sensor "' + str(submitted_juvo_id) + '" for ' + submitted_name + '. Click <a href="/admin/sensor" class="alert-link">here</a> to view/edit responses.'
            flash(Markup(response))
            previous = 1
            return redirect(url_for('create_sensor'))

    return render_template('create_sensor_form.html', form=form, form2=form2, current=previous, list1=list1, list2=list2)
