import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from flask import Flask, flash, redirect, render_template, request, abort, session

# internal imports
from app import app, server
from apps import dashboard
# from apps import input_data, dashboard, reports

global current_page
current_page = 'dashboard'

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        html.Nav([
            html.Div([
                html.Ul([
                    html.Li([
                        html.Div([
                            dcc.Link('Dashboard', href='/dashboard')
                        ], className='nav-link')
                    ], className='nav-item'),
                    html.Li([
                        html.Div([
                            html.A('Shift Reports', href='/reports')
                            # {isActive}'.format(isActive = ' active' if current_page == 'reports' else ''), href='/reports')
                        ], className='nav-link')
                    ], className='nav-item'),
                    html.Li([
                        html.Div([
                            html.A(html.Button('Log Out!'), href='/logout')
                        ], className='nav-link')
                    ], className='nav-item')
                ], className='nav flex-column')
            ], className='sidebar-sticky')
        ], className='col-md-2 sidebar'),
        html.Div(id='page-content', className='col-md-10 ml-sm-auto col-lg-10')  # this is where the page content goes
    ], className='row')
], className='container-fluid')


@server.route('/app1')
def dashboard2():
    print("here")
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return app.index()

@server.route('/reports')
def reports_method():
    print("here reports")
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return "render reports template here"

# @app.callback(Output('page-content', 'children'),
              # [Input('url', 'pathname')])
# def display_page(pathname):
    # if pathname == '/app1' or pathname == '/dashboard':
        # if not session.get('logged_in'):
            # return render_template('login.html')
        # else:
            # current_page = 'dashboard'
            # return app.layout
    # elif pathname == '/reports':
        # current_page = 'reports'
        # return reports.layout
    # else:
        # return '404'


if __name__ == '__main__':
    server.run(debug=True)
