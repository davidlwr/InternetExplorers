import os
from flask import Flask, request, redirect
from flask_login import LoginManager, UserMixin, login_user, logout_user
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash import Dash

from dash_flask_login import FlaskLoginAuth

server = Flask(__name__)

# config
server.config.update(
    SECRET_KEY=os.urandom(12),
)

app = Dash(name='app1', url_base_pathname='/app1', server=server)
# server = app.server
app.config.suppress_callback_exceptions = True


# Bootstrap sample template for css
css_source = ['https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css',
              'https://codepen.io/bricakeld/pen/qKZeGq.css']
for css in css_source:
    app.css.append_css({'external_url': css})

# Setup the LoginManager for the server
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "/login"


# callback to reload the user object
@login_manager.user_loader
def load_user(userid):
    return User(userid)


# Create our initial Dash App
# app = Dash(name='app1', url_base_pathname='/app1', server=server)
#

# Create Login Dash App with a login form
login_app = Dash(name='login-app', url_base_pathname='/login', server=server)

login_app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css',
})

login_app.layout = html.Div([
    html.H1('Please log in to continue.', id='h1'),
    html.Form(
        method='Post',
        children=[
            dcc.Input(
                placeholder='Enter your username',
                type='text',
                id='uname-box'
            ),
            dcc.Input(
                placeholder='Enter your password',
                type='password',
                id='pwd-box'
            ),
            html.Button(
                children='Login',
                n_clicks=0,
                type='submit',
                id='submit-button'
            ),

        ]
    ),
    html.A(html.Button('app1'), href='/dashboard', style={'display': 'none'}, id='hidden-link')
]
)


# This callback to the login app should encapsulate the login functionality
# Set the output to a non-visible location
@login_app.callback(
    Output('h1', 'n_clicks'),
    [Input('submit-button', 'n_clicks')],
    [State('uname-box', 'value'),
     State('pwd-box', 'value')]
)
def login(n_clicks, uname, pwd):
    if uname == 'user' and pwd == 'password':
        login_user(load_user(users[0].name))

    else:
        pass


# Create logout Dash App
logout_app = Dash(name='logout-app', url_base_pathname='/logout', server=server)

logout_app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css',
})

logout_app.layout = html.Div([
    html.H1('You have successfully logged out!', id='h1'),

    # Since we've logged out, this will force a redirect to the login page with a next page of /app1
    html.A(html.Button('Log Back In'), href='/app1', id='login-button'),
]
)


# This callback to the logout app simply logs the user out each time the logout page is loaded
@logout_app.callback(
    Output('h1', 'n_clicks'),
    [Input('login-button', 'children')]
)
def logout(children):
    logout_user()


# Create FlaskLoginAuth object to require login for Dash Apps
auth = FlaskLoginAuth(app)

# Add logout app to FlaskLoginAuth
auth.add_app(logout_app)


# Create User class with UserMixin
class User(UserMixin):

    def __init__(self, id):
        self.id = id
        self.name = "user" + str(id)
        self.password = self.name + "_secret"

    def __repr__(self):
        return "%d/%s/%s" % (self.id, self.name, self.password)


# Create some users
users = [User(id) for id in range(1, 21)]


# Adding this route allows us to use the POST method on our login app.
# It also allows us to implement HTTP Redirect when the login form is submitted.
@server.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.args.get('next'):
            return redirect(request.args.get('next'))
        else:
            return redirect('/login')
    else:
        return redirect('/login')
