import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd

# internal imports
from app import app, server
from apps import input_data, dashboard, reports, residents_overview, sample_form

global current_page
current_page = 'dashboard'

# residents app
# residents_app = dash.Dash(__name__, server=app.server, url_base_pathname='/residents')

@server.route("/dashboard", methods=['GET', 'POST'])
def show_dashboard():
    return app.index()

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
