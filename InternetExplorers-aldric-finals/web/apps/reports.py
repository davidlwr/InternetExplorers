import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# internal imports
from app import app

# define page layout
layout = html.Main([
    html.Div([
        html.Div([
            html.H1('End-of-Shift Reports')
        ], className='row'),
        html.Div([
            html.P('View by shifts or by residents below:')
        ], className = 'row'),
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id='reports_location_input',
                    options=['hello test', 'hello bye'],
                    placeholder='Select a location to view'
                )
            ], className = 'col-md-6'),
            html.Div([
                'Put some date selector here'
            ], className = 'col-md-6')
        ], className = 'row'),
        html.Div([
            html.Div(id='report_overview_output', className = 'col-md-12')
        ], className = 'row')
    ], className = 'col-md-12')
], role = 'main')
