import dash
import flask
from flask_sqlalchemy import SQLAlchemy
from flask import url_for

# NOTE: might need to rename the main flask app to 'app' to be compatible with deployment,
#+then rename the dash app to something else
server = flask.Flask(__name__)
server.config['SECRET_KEY'] = 'userandomtogeneratesomethinghere'
server.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://internetexplorer:int3rn3t@127.0.0.1:3306/stbern'
# server.config['SERVER_NAME'] = 'IExStBern'
db = SQLAlchemy(server)

# default app
app = dash.Dash(__name__, server=server, url_base_pathname='/insertsomeotherrandomstringhere')
# server = app.server
app.config.suppress_callback_exceptions = True
csspath = ''

with server.test_request_context():
    csspath = url_for('static', filename='extra.css')
# Bootstrap sample template for css
css_source = ['https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css',
              csspath]
for css in css_source:
    app.css.append_css({'external_url': css})
