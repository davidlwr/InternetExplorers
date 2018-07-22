from dash.dependencies import Input, Output
import pandas as pd
import flask_login
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask import render_template, Flask, request, flash
from flask_sqlalchemy import SQLAlchemy

# internal imports
from app import app, server
from apps import input_data, dashboard, reports, residents_overview, sample_form

login_manager = flask_login.LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('Remember me?')

# residents app
# residents_app = dash.Dash(__name__, server=app.server, url_base_pathname='/residents')

@login_manager.user_loader
def load_user(user_id):
    pass

@server.route("/graphs", methods=['GET', 'POST'])
@server.route("/", methods=['GET', 'POST'])
@flask_login.login_required
def show_dashboard():
    return app.index()

@server.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # handle logic here

        # if wrong username or password
        flash('Invalid username or password')
        return render_template('login.html', form=form)

    # else if fail authentication
    return render_template('login.html', form=form)

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
    app.run_server(debug=True)
