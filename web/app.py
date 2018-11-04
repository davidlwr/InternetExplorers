import dash
import flask
from flask_sqlalchemy import SQLAlchemy
from flask import url_for
import sys
from datetime import datetime
from werkzeug.routing import BaseConverter, ValidationError

# NOTE: might need to rename the main flask app to 'app' to be compatible with deployment,
#+then rename the dash app to something else
server = flask.Flask(__name__)
server.config['SECRET_KEY'] = 'userandomtogeneratesomethinghere'
server.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://internetexplorer:int3rn3t@127.0.0.1:3306/stbern'
server.jinja_env.trim_blocks = True # remove whitespaces
server.jinja_env.lstrip_blocks = True # remove whitespaces
if sys.platform == 'linux':
    server.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://internetexplorer:int3rn3t@stbern.cdc1tjbn622d.ap-southeast-1.rds.amazonaws.com:3306/stbern'
# server.config['SERVER_NAME'] = 'IExStBern'
db = SQLAlchemy(server)

class DateConverter(BaseConverter):
    """
    Extracts a ISO8601 date from the path and validates it.
    from https://stackoverflow.com/questions/31669864/date-in-flask-url
    """

    regex = r'\d{4}-\d{2}-\d{2}'

    def to_python(self, value):
        try:
            return datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            raise ValidationError()

    def to_url(self, value):
        return value.strftime('%Y-%m-%d')

server.url_map.converters['date'] = DateConverter

# default app
app = dash.Dash(__name__, server=server, url_base_pathname='/insertsomeotherrandomstringhere')
# server = app.server
app.config.suppress_callback_exceptions = True
csspath1 = ''
csspath2 = ''
csspath3 = ''
jspath1 = ''
jspath2 = ''
csspath4 = ''

with server.test_request_context():
    csspath1 = url_for('static', filename='bootstrap.css')
    csspath2 = url_for('static', filename='sb-admin-2.css')
    csspath3 = url_for('static', filename='metis-menu.min.css')
    ### uncomment in deployed app, comment for local
    # csspath4 = """">
    # <!-- Global site tag (gtag.js) - Google Analytics -->
    # <script async src="https://www.googletagmanager.com/gtag/js?id=UA-125800418-1"></script>
    # <script>
    #   window.dataLayer = window.dataLayer || [];
    #   function gtag(){dataLayer.push(arguments);}
    #   gtag('js', new Date());
    #
    #   gtag('config', 'UA-125800418-1');
    # </script>
    # <"
    # """
    jspath1 = url_for('static', filename='metis-menu.min.js')
    jspath2 = url_for('static', filename='sb-admin-2.js')
    # jspath3 = url_for('static', filename='googleanalytics.js')

# Bootstrap sample template for css
css_source = [csspath4, 'https://fonts.googleapis.com/icon?family=Material+Icons', csspath1, csspath2, csspath3, 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css']
for css in css_source:
    app.css.append_css({'external_url': css})

js_source = ['https://blackrockdigital.github.io/startbootstrap-sb-admin-2/vendor/jquery/jquery.min.js', 'https://blackrockdigital.github.io/startbootstrap-sb-admin-2/vendor/bootstrap/js/bootstrap.min.js', jspath1, jspath2]
for jspath in js_source:
    app.scripts.append_script({'external_url': jspath})
