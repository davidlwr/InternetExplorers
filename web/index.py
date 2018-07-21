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
                            dcc.Link('Shift Reports', href='/reports')
                            # {isActive}'.format(isActive = ' active' if current_page == 'reports' else ''), href='/reports')
                        ], className='nav-link')
                    ], className='nav-item'),
                    html.Li([
                        html.Div([
                            html.A('Residents Overview', href='/anotherflask')
                            # {isActive}'.format(isActive = ' active' if current_page == 'reports' else ''), href='/reports')
                        ], className='nav-link')
                    ], className='nav-item')
                ], className='nav flex-column')
            ], className='sidebar-sticky')
        ], className='col-md-2 sidebar'),
        html.Div(id='page-content', className='col-md-10 ml-sm-auto col-lg-10')  # this is where the page content goes
    ], className='row')
], className='container-fluid')


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/' or pathname == '/dashboard':
        current_page = 'dashboard'
        return dashboard.layout
    elif pathname == '/reports':
        current_page = 'reports'
        return reports.layout
    elif pathname == '/residents':
        current_page = 'residents overview'
        return residents_overview.layout
    else:
        return '404'


if __name__ == '__main__':
    app.run_server(debug=True)
