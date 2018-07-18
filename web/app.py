from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
from dash import Dash
 
server = Flask(__name__)

# config
server.config.update(
    SECRET_KEY=os.urandom(12),
)

app = Dash(name='app1', url_base_pathname='/hello12344567adssda', server=server)
# server = app.server
app.config.suppress_callback_exceptions = True



@server.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return "Hello Boss!  <a href='/logout'>Logout</a>"
 
@server.route('/login', methods=['POST'])
def do_admin_login():
    if request.form['password'] == 'password' and request.form['username'] == 'admin':
        session['logged_in'] = True
    else:
        flash('wrong password!')
    return home()
 
@server.route("/logout")
def logout():
    session['logged_in'] = False
    return home()

if __name__ == "__main__":
    server.secret_key = os.urandom(12)
    app.run_server(debug=True)