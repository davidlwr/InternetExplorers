from dash.dependencies import Input, Output
import pandas as pd
import flask_login
import hashlib
import secrets
import string
from flask.json import dump
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, RadioField, FloatField, SelectField, HiddenField
from flask_login import UserMixin, current_user, LoginManager, AnonymousUserMixin
from flask_admin import Admin, AdminIndexView, helpers, expose
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextField
from wtforms.validators import InputRequired, Email, Length, ValidationError
from flask import render_template, Flask, request, flash, redirect, url_for, abort, session
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import urlparse, urljoin
from dash_flask_login import FlaskLoginAuth
import sys
from werkzeug.security import generate_password_hash, check_password_hash

# internal imports
from app import app, server, db
from apps import input_data, dashboard, reports, residents_overview, shift_log_form, risk_assessment_form
from apps.shift_log_form import Resident
from Entities.user import User
from DAOs.user_DAO import user_DAO

login_manager = flask_login.LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'

# Create FlaskLoginAuth object to require login for Dash Apps
auth = FlaskLoginAuth(app)


class Anonymous(AnonymousUserMixin):
    def __init__(self):
        self.staff_type = 'Guest'


login_manager.anonymous_user = Anonymous


# class Resident(db.Model):
#     resident_id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100))
#     node_ide = db.Column(db.String(20))
#     age = db.Column(db.Integer)
#     fall_risk = db.Column(db.String(45))
#     status = db.Column(db.String(45))
#     stay_location = db.Column(db.String(45))


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
    staff_type = SelectField('Staff Type',
                             choices=[('Staff', 'Staff'), ('Admin', 'Admin')])

    def get_user(self):
        return db.session.query(User).filter_by(username=self.username.data).first()


class EditForm(Form):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=25)])
    name = StringField('Name')
    email = StringField('Email')
    staff_type = StringField('Staff Type')

    def get_user(self):
        return db.session.query(User).filter_by(username=self.username.data).first()


class MyModelView(ModelView):
    column_display_pk = True
    column_default_sort = 'username'
    column_exclude_list = ('encrypted_password', 'encrypted_password_token')

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
        return redirect(url_for('show_graphs'))

    def get_create_form(self):
        return CreateForm

    def get_edit_form(self):
        return EditForm

    # def get_delete_form(self):
    #     return CreateForm

    def validate_form(self, form):
        try:
            if form.validate_on_submit() and form.encrypted_password.data:
                encrypted_password = form.encrypted_password.data
                alphabet = string.ascii_letters + string.digits
                encrypted_password_token = ''.join(secrets.choice(alphabet) for i in range(20))
                encrypted_password = (encrypted_password_token + encrypted_password).encode('utf-8')
                encrypted_password = hashlib.sha512(encrypted_password).hexdigest()
                form.encrypted_password.data = encrypted_password
                form.encrypted_password_token.data = encrypted_password_token
        except:
            return super(MyModelView, self).validate_form(form)

        return super(MyModelView, self).validate_form(form)


class ResidentView(ModelView):
    print("submitted2")

    def is_accessible(self):
        if current_user.staff_type == 'Admin' or current_user.staff_type == 'Staff':
            return True

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('show_graphs'))

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


class MyAdminIndexView(AdminIndexView):

    def is_accessible(self):
        return True


# class MyAdminIndexView(AdminIndexView):
#     def is_accessible(self):
#         return current_user.is_authenticated
#
#     @expose('/')
#     def index(self):
#         if not current_user.is_authenticated:
#             return redirect(url_for('.login_view'))
#         return super(MyAdminIndexView, self).index()
#
#     @expose('/login/', methods=('GET', 'POST'))
#     def login_view(self):
#         # handle user login
#         form = LoginForm()
#         if helpers.validate_form_on_submit(form):
#             user = form.get_user()
#             flask_login.login_user(user)
#
#         if current_user.is_authenticated:
#             return redirect(url_for('.index'))
#         link = '<p>Don\'t have an account? <a href="' + url_for('.register_view') + '">Click here to register.</a></p>'
#         self._template_args['form'] = form
#         self._template_args['link'] = link
#         return super(MyAdminIndexView, self).index()
#
#     @expose('/register/', methods=('GET', 'POST'))
#     def register_view(self):
#         form = RegistrationForm(request.form)
#         if helpers.validate_form_on_submit(form):
#             user = User()
#
#             form.populate_obj(user)
#             # we hash the users password to avoid saving it as plaintext in the db,
#             # remove to use plain text:
#             user.password = generate_password_hash(form.password.data)
#
#             db.session.add(user)
#             db.session.commit()
#
#             flask_login.login_user(user)
#             return redirect(url_for('.index'))
#         link = '<p>Already have an account? <a href="' + url_for('.login_view') + '">Click here to log in.</a></p>'
#         self._template_args['form'] = form
#         self._template_args['link'] = link
#         return super(MyAdminIndexView, self).index()
#
#     @expose('/logout/')
#     def logout_view(self):
#         flask_login.logout_user()
#         return redirect(url_for('.index'))


admin = Admin(server, index_view=MyAdminIndexView(), base_template='my_master.html')
admin.add_view(MyModelView(User, db.session))
admin.add_view(ResidentView(Resident, db.session))


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


# residents app
# residents_app = dash.Dash(__name__, server=app.server, url_base_pathname='/residents')

@login_manager.user_loader
def load_user(user_name):
    return User.query.get(user_name)


@server.route("/graphs", methods=['GET', 'POST'])
@flask_login.login_required
def show_graphs():
    return app.index()


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

            return redirect(next or url_for('show_graphs'))
        # if wrong username or password
        flash('Invalid username or password')
        return render_template('login.html', form=form)

    # else if fail authentication
    return render_template('login.html', form=form)


@server.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect(url_for('show_graphs'))  # NOTE: replace with some index page next time


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
