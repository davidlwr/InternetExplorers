from dash.dependencies import Input, Output
import pandas as pd
import flask_login
import hashlib
import secrets
import string
from flask.json import dump
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, RadioField, FloatField, SelectField, HiddenField, \
    IntegerField
from flask_login import UserMixin, current_user, LoginManager, AnonymousUserMixin
from flask_admin import Admin, AdminIndexView, helpers, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.model import typefmt
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextField
from wtforms.validators import InputRequired, Email, Length, ValidationError
from flask import render_template, Flask, request, flash, redirect, url_for, abort, session, Markup
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import urlparse, urljoin
from dash_flask_login import FlaskLoginAuth
from datetime import datetime, date
from DAOs.sensor_DAO import sensor_DAO
from sensor_mgmt.JuvoAPI import JuvoAPI
import sys
from werkzeug.security import generate_password_hash, check_password_hash

# internal imports
from app import app, server, db
from apps import input_data, input_shiftlogs, dashboard, reports, residents_overview, shift_log_form, \
    risk_assessment_form, change_password_form
from apps.shift_log_form import Resident, ShiftLogForm
from apps.create_sensor_form import SensorCreateForm, BedSensorCreateForm
from apps.risk_assessment_form import RiskAssessmentForm
from Entities.user import User
from DAOs.user_DAO import user_DAO
from DAOs import resident_DAO
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select, func, case
from wtforms.fields.html5 import DateField

login_manager = flask_login.LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'

# Create FlaskLoginAuth object to require login for Dash Apps
auth = FlaskLoginAuth(app)

### DEFINE global methods for jinja to use
@server.context_processor
def custom_jinja_global_variables():
    def get_list_of_residents_jinja(filter_active=True, location_filter='BKT'):
        return resident_DAO.get_list_of_residents(filter_active, location_filter)
    return dict(all_residents=get_list_of_residents_jinja)

class Anonymous(AnonymousUserMixin):
    def __init__(self):
        self.staff_type = 'Guest'


login_manager.anonymous_user = Anonymous


class Shift_log(db.Model):
    datetime = db.Column(db.DateTime, primary_key=True)
    patient_id = db.Column(db.Integer, primary_key=True)
    # resident_object = db.relationship('Resident', backref='Shift_log', lazy=True, uselist=False)
    num_falls = db.Column(db.Integer)
    num_near_falls = db.Column(db.Integer)
    food_consumption = db.Column(db.String(45))
    num_toilet_visit = db.Column(db.Integer)
    temperature = db.Column(db.Float)
    systolic_bp = db.Column(db.Float)
    diastolic_bp = db.Column(db.Float)
    pulse_rate = db.Column(db.Float)

    @hybrid_property
    def resident_name(self):
        resident_object = db.session.query(Resident).filter_by(resident_id=self.patient_id).first()
        return resident_object.name

    @resident_name.expression
    def resident_name(cls):
        return select([Resident.name]).where(Resident.resident_id == cls.patient_id)


class Risk_assessment(db.Model):
    datetime = db.Column(db.DateTime, primary_key=True)
    patient_id = db.Column(db.Integer, primary_key=True)
    # resident_object = db.relationship('Resident', backref='risk_assessment', lazy=True, uselist=False, cascade="save-update, delete-orphan")
    weight = db.Column(db.Float)
    num_falls = db.Column(db.Integer)
    injury_sustained = db.Column(db.Integer)
    mbs_normal = db.Column(db.Integer)
    mbs_confusion = db.Column(db.Integer)
    mbs_restlessness = db.Column(db.Integer)
    mbs_agitation = db.Column(db.Integer)
    mbs_uncooperative = db.Column(db.Integer)
    mbs_hallucination = db.Column(db.Integer)
    mbs_drowsy = db.Column(db.Integer)
    mbs_others = db.Column(db.String(100))
    mbs_status = db.Column(db.Integer)
    ast_medication = db.Column(db.Integer)
    ast_clothes = db.Column(db.Integer)
    ast_eating = db.Column(db.Integer)
    ast_bathing = db.Column(db.Integer)
    ast_walking = db.Column(db.Integer)
    ast_toileting = db.Column(db.Integer)
    ast_others = db.Column(db.String(100))
    pain_level = db.Column(db.Integer)
    pain_other = db.Column(db.String(100))
    num_medication = db.Column(db.Integer)
    num_medicalCondition = db.Column(db.Integer)
    hearing_ability = db.Column(db.Integer)
    vision_ability = db.Column(db.Integer)
    mobility = db.Column(db.Integer)
    dependency = db.Column(db.Integer)
    dependency_comments = db.Column(db.String(100))
    total_score = db.Column(db.Integer)

    @hybrid_property
    def resident_name(self):
        resident_object = db.session.query(Resident).filter_by(resident_id=self.patient_id).first()
        return resident_object.name

    @resident_name.expression
    def resident_name(cls):
        return select([Resident.name]).where(Resident.resident_id == cls.patient_id)


class User(db.Model):
    username = db.Column(db.String(45), primary_key=True)
    name = db.Column(db.String(45))
    email = db.Column(db.String(45))
    encrypted_password = db.Column(db.String(45))
    encrypted_password_token = db.Column(db.String(45))
    staff_type = db.Column(db.String(45))

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username


class CreateForm(Form):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=25)])
    name = StringField('Name')
    email = StringField('Email')
    encrypted_password = PasswordField('Password', validators=[InputRequired(), Length(min=8)])
    encrypted_password_token = HiddenField()
    staff_type = SelectField('User Type',
                             choices=[('Staff', 'Staff'), ('Admin', 'Admin')])

    def get_user(self):
        return db.session.query(User).filter_by(username=self.username.data).first()


class EditForm(Form):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=25)])
    name = StringField('Name')
    email = StringField('Email')
    staff_type = StringField('User Type',
                             choices=[('Staff', 'Staff'), ('Admin', 'Admin')])

    def get_user(self):
        return db.session.query(User).filter_by(username=self.username.data).first()


class MyModelView(ModelView):
    column_labels = dict(staff_type='User Type')
    column_display_pk = True
    column_default_sort = 'username'
    column_exclude_list = ('encrypted_password', 'encrypted_password_token')
    form_edit_rules = ('name', 'email', 'staff_type')

    # column_editable_list = ( 'name', 'email', 'staff_type')
    # @expose('/register/', methods=('GET', 'POST'))
    # def register_view(self):
    #     form = CreateForm(request.form)
    #     if form.validate_on_submit():
    #         print("submitted2")

    def is_accessible(self):
        if current_user.staff_type == 'Admin':
            return True

    def inaccessible_callback(self, name, **kwargs):
        flash('You do not have the user rights to access this page!')
        return redirect(url_for('show_graphs'))

    def get_create_form(self):
        return CreateForm

    # def get_edit_form(self):
    #     return EditForm

    # def get_delete_form(self):
    #     return CreateForm

    def validate_form(self, form):

        try:
            encrypted_password = form.encrypted_password.data

            if user_DAO.get_user_by_id(form.username.data) is not None:
                flash('The username is already in use')
                return

            if form.validate_on_submit() and encrypted_password:
                alphabet = string.ascii_letters + string.digits
                encrypted_password_token = ''.join(secrets.choice(alphabet) for i in range(20))
                encrypted_password = (encrypted_password_token + encrypted_password).encode('utf-8')
                encrypted_password = hashlib.sha512(encrypted_password).hexdigest()
                form.encrypted_password.data = encrypted_password
                form.encrypted_password_token.data = encrypted_password_token
        except:
            return super(MyModelView, self).validate_form(form)

        return super(MyModelView, self).validate_form(form)


class ResidentCreateForm(Form):
    name = StringField('Name')
    node_id = StringField('Node')
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[InputRequired('Please enter date!')])
    fall_risk = StringField('Fall Risk')
    status = StringField('Status')
    stay_location = RadioField('Stay Location',
                               choices=[('bkttm', 'Bukit Timah'), ('adm', 'Adam Road')])


def date_format(view, value):
    return value.strftime('%Y-%m-%d')


MY_DEFAULT_FORMATTERS = dict(typefmt.BASE_FORMATTERS)
MY_DEFAULT_FORMATTERS.update({
    date: date_format
})


class ResidentView(ModelView):
    # column_list = ('name', 'node_id', 'age', 'fall_risk', 'status', 'stay_location')
    column_type_formatters = MY_DEFAULT_FORMATTERS

    def is_accessible(self):
        if current_user.staff_type == 'Admin' or current_user.staff_type == 'Staff':
            return True

    def inaccessible_callback(self, name, **kwargs):
        flash('You do not have the user rights to access this page!')
        return redirect(url_for('show_graphs'))

    def get_create_form(self):
        return ResidentCreateForm

    def get_edit_form(self):
        return ResidentCreateForm

    # def validate_form(self, form):
    #     try:
    #         if form.validate_on_submit() and form.encrypted_password.data:
    #             encrypted_password = form.encrypted_password.data
    #             alphabet = string.ascii_letters + string.digits
    #             encrypted_password_token = ''.join(secrets.choice(alphabet) for i in range(20))
    #             encrypted_password = (encrypted_password_token + encrypted_password).encode('utf-8')
    #             encrypted_password = hashlib.sha512(encrypted_password).hexdigest()
    #             form.encrypted_password.data = encrypted_password
    #             form.encrypted_password_token.data = encrypted_password_token
    #     except:
    #         return super(MyModelView, self).validate_form(form)
    #
    #     return super(MyModelView, self).validate_form(form)


# def user_link_formatter(view, context, model, name):
#     field = getattr(model, name)
#     url = url_for('user.details_view', id=field.id)
#     return Markup('<a href="{}">{}</a>'.format(url, field))


class FormView(ModelView):
    #
    # def create_form(self):
    #     ShiftLogForm()
    # can_create = False
    form_excluded_columns = 'resident_object'
    column_display_pk = True
    column_default_sort = ('datetime', True)
    column_list = (
        'datetime', 'patient_id', 'resident_name', 'num_falls', 'num_near_falls', 'food_consumption',
        'num_toilet_visit', 'temperature', 'systolic_bp', 'diastolic_bp', 'pulse_rate')
    column_sortable_list = (
        'datetime', 'patient_id', 'resident_name', 'num_falls', 'num_near_falls', 'food_consumption',
        'num_toilet_visit', 'temperature', 'systolic_bp', 'diastolic_bp', 'pulse_rate')

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        form = ShiftLogForm()
        return render_template('eosforms.html', form=form)

    # def get_create_form(self):
    #     return ShiftLogForm

    # create_template = 'createLogForm.html'

    def is_accessible(self):
        if current_user.staff_type == 'Admin' or current_user.staff_type == 'Staff':
            return True

    def inaccessible_callback(self, name, **kwargs):
        flash('You do not have the user rights to access this page!')
        return redirect(url_for('showForms'))


class RiskAssessmentView(ModelView):
    form_excluded_columns = 'resident_object'
    column_display_pk = True
    column_default_sort = ('datetime', True)
    column_list = (
        'datetime', 'patient_id', 'resident_name', 'weight', 'num_falls', 'injury_sustained', 'mbs_normal',
        'mbs_confusion',
        'mbs_restlessness', 'mbs_agitation', 'mbs_uncooperative', 'mbs_hallucination', 'mbs_drowsy', 'mbs_others',
        'mbs_status', 'ast_medication', 'ast_clothes', 'ast_eating', 'ast_bathing', 'ast_walking', 'ast_toileting',
        'ast_others', 'pain_level', 'pain_other', 'num_medication', 'num_medicalCondition', 'hearing_ability',
        'vision_ability', 'mobility', 'dependency', 'dependency_comments', 'total_score')
    column_sortable_list = (
        'datetime', 'patient_id', 'resident_name', 'weight', 'num_falls', 'injury_sustained', 'mbs_normal',
        'mbs_confusion',
        'mbs_restlessness', 'mbs_agitation', 'mbs_uncooperative', 'mbs_hallucination', 'mbs_drowsy', 'mbs_others',
        'mbs_status', 'ast_medication', 'ast_clothes', 'ast_eating', 'ast_bathing', 'ast_walking', 'ast_toileting',
        'ast_others', 'pain_level', 'pain_other', 'num_medication', 'num_medicalCondition', 'hearing_ability',
        'vision_ability', 'mobility', 'dependency', 'dependency_comments', 'total_score')

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        form = RiskAssessmentForm()
        return render_template('raforms.html', form=form, currentDate=datetime.now().strftime('%Y-%m'))

    def is_accessible(self):
        if current_user.staff_type == 'Admin':
            return True

    def inaccessible_callback(self, name, **kwargs):
        flash('You do not have the user rights to access this page!')
        return redirect(url_for('showRiskForm'))


class Sensor(db.Model):
    uuid = db.Column(db.String(45), primary_key=True)
    type = db.Column(db.String(45))
    location = db.Column(db.String(45))
    description = db.Column(db.String(45))
    juvo_target = db.Column(db.Integer)
    facility_abrv = db.Column(db.String(45))


# class SensorCreateForm(Form):
#     uuid = StringField('uuid')
#     type = StringField('type')
#     location = StringField('location')
#     description = StringField('description')
#     juvo_target = IntegerField('juvo target')
#     facility_abrv = StringField('facility abbreviation')


class SensorView(ModelView):
    column_display_pk = True

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        form = SensorCreateForm()
        uuid_list = sensor_DAO.get_unregistered_uuids()
        form.uuid.choices = [(uuid, uuid) for uuid in uuid_list]
        if len(uuid_list) == 0:
            list1 = "0"
        else:
            list1 = "1"

        form2 = BedSensorCreateForm()
        juvo_id_list = JuvoAPI.get_unregistered_sensors()
        form2.juvo_id.choices = [(juvo_id, juvo_id) for juvo_id in juvo_id_list]
        if len(juvo_id_list) == 0:
            list2 = "0"
        else:
            list2 = "1"

        return render_template('create_sensor_form.html', form=form, form2=form2, current=0, list1=list1, list2=list2)

    def is_accessible(self):
        if current_user.staff_type == 'Admin':
            return True

    def inaccessible_callback(self, name, **kwargs):
        flash('You do not have the user rights to access this page!')
        return redirect(url_for('showRiskForm'))


class MyAdminIndexView(AdminIndexView):

    @expose('/', methods=('GET', 'POST'))
    def create_view(self):
        return redirect(url_for('showOverviewResidents'))

    def is_visible(self):
        return False

    def is_accessible(self):
        return True


admin = Admin(server, name='Home', index_view=MyAdminIndexView(), base_template='my_master.html')
admin.add_view(MyModelView(User, db.session, 'User'))
admin.add_view(ResidentView(Resident, db.session, 'Residents'))
admin.add_view(FormView(Shift_log, db.session, 'Shift Logs'))
admin.add_view(RiskAssessmentView(Risk_assessment, db.session, 'Risk Assessment Forms'))
admin.add_view(SensorView(Sensor, db.session, 'Sensors'))


# utlity method for security
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    remember = BooleanField('Remember me?')

    def get_user(self):
        return db.session.query(User).filter_by(login=self.username.data).first()


@login_manager.user_loader
def load_user(user_name):
    return User.query.get(user_name)


@server.route("/graphs", methods=['GET', 'POST'])
@flask_login.login_required
def show_graphs():
    # input_data.updateInputData()
    # return app.index()
    return render_template('detailed_graphs.html')


@server.route("/reports")
def show_reports():
    return "Not implemented yet!<br/>You don't need to login to see this<br/><a href='/'>Go to main graphs</a>"


@server.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # handle logic here
        authenticate_user = user_DAO.authenticate(form.username.data, form.password.data)

        if authenticate_user:
            user = User.query.get(form.username.data)
            flask_login.login_user(user, remember=form.remember.data)

            next = request.args.get('next')
            print("DEBUG:", next)
            # is_safe_url should check if the url is safe for redirects.
            # See http://flask.pocoo.org/snippets/62/ for an example.
            if not is_safe_url(next):
                print("DEBUG: LOG: url marked as unsafe")
                return abort(400)

            return redirect(next or url_for('showOverviewResidents'))
        # if wrong username or password
        flash('Invalid username or password')
        return render_template('login.html', form=form)

    # else if fail authentication
    return render_template('login.html', form=form)


@server.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect(url_for('login'))  # NOTE: replace with some index page next time


# @app.callback(Output('page-content', 'children'),
#               [Input('url', 'pathname')])
# def display_page(pathname):
#     if pathname == '/':
#         current_page = 'dashboard'
#         return dashboard.layout
#     elif pathname == '/reports':
#         current_page = 'reports'
#         return reports.layout
#     elif pathname == '/residents':
#         current_page = 'residents overview'
#         return residents_overview.layout
#     else:
#         return '404'

if __name__ == '__main__':
    if sys.platform == 'linux':
        app.run_server(host='0.0.0.0', port=80, debug=True)
    else:
        app.run_server(debug=True)
