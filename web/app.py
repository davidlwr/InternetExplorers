import dash
import flask

server = flask.Flask(__name__)
server.config['SECRET_KEY'] = 'userandomtogeneratesomethinghere'
server.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://internetexplorer:int3rn3t@127.0.0.1:3306/stbern'


# default app
app = dash.Dash(__name__, server=server, url_base_pathname='/insertsomeotherrandomstringhere')
# server = app.server
app.config.suppress_callback_exceptions = True

# Bootstrap sample template for css
css_source = ['https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css',
              'https://codepen.io/bricakeld/pen/qKZeGq.css']
for css in css_source:
    app.css.append_css({'external_url': css})
