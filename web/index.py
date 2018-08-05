from dash.dependencies import Input, Output
import pandas as pd
import flask_login
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask import render_template, Flask, request, flash, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import urlparse, urljoin
from dash_flask_login import FlaskLoginAuth
import sys

# internal imports
from app import app, server
from apps import input_data, dashboard, reports, residents_overview, sample_form
from Entities.user import User
from DAOs.user_DAO import user_DAO

login_manager = flask_login.LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'

# Create FlaskLoginAuth object to require login for Dash Apps
auth = FlaskLoginAuth(app)

# utlity method for security
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

u_DAO = user_DAO()

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('Remember me?')

# residents app
# residents_app = dash.Dash(__name__, server=app.server, url_base_pathname='/residents')

@login_manager.user_loader
def load_user(user_name):
    return u_DAO.get_user_by_id(user_name)

@server.route("/graphs", methods=['GET', 'POST'])
@server.route("/", methods=['GET', 'POST'])
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
        authed_user = u_DAO.authenticate(form.username.data, form.password.data)
        if authed_user:
            flask_login.login_user(authed_user, remember=form.remember.data)
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
    return redirect(url_for('show_graphs')) # NOTE: replace with some index page next time

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
