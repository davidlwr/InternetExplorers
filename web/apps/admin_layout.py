import dash_core_components as dcc
import dash_html_components as html
from app import app
from apps import input_data
import datetime
locationMap = input_data.get_location_options()

layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        html.Nav([
            html.Div([
                html.Ul([
                    html.Li([
                        html.Div([
                            html.A('Graphs', href='/graphs')
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
                            html.A('End of Shift Forms', href='/eosforms')
                        ], className='nav-link')
                    ], className='nav-item'),
                    html.Li([
                        html.Div([
                            html.A('Risk Assessment Forms', href='/raforms')
                        ], className='nav-link')
                    ], className='nav-item'),
                    html.Li([
                        html.Div([
                            html.A('Admin', href='/admin')
                        ], className='nav-link')
                    ], className='nav-item'),
                    html.Li([
                        html.Div([
                            html.A('Logout', href='/logout')
                        ], className='nav-link')
                    ], className='nav-item')
                ], className='nav flex-column')
            ], className='sidebar-sticky')
        ], className='col-md-2 sidebar col-xs-12'),
        html.Main([
            html.Div([
                html.Div([
                    html.H1('Home Page')
                ], className='row'),
                html.Div([
                    html.Div([
                        html.H3('View resident\'s activity')
                    ], className='row'),
                    html.Div([
                        html.Div([
                            dcc.Dropdown(
                                id='resident_input',
                                options=[{'label': i, 'value': i} for i in input_data.get_residents_options()],
                                placeholder='Select a resident to view'
                            )
                        ], className='col-md-4'),
                        html.Div([
                            dcc.Dropdown(
                                id='location_input',
                                options=[{'label': i, 'value': locationMap[i]} for i in locationMap],
                                placeholder='Select a location to view'
                            )
                        ], className='col-md-4'),
                        html.Div([
                            dcc.DatePickerRange(
                                id='date_picker',
                                min_date_allowed=input_data.input_raw_min_date,
                                max_date_allowed=input_data.input_raw_max_date,
                                start_date=input_data.input_raw_min_date.replace(hour=0, minute=0, second=0,
                                                                                 microsecond=0),
                                # need to truncate the dates here
                                end_date=input_data.input_raw_max_date.replace(hour=0, minute=0, second=0,
                                                                               microsecond=0),
                                # to prevent unconverted data error
                                start_date_placeholder_text='Select start date',
                                end_date_placeholder_text='Select end date',
                                minimum_nights=0
                            )
                        ], className='col-md-4')
                    ], className='row'),
                    html.Div([
                        html.Div([
                            dcc.Checklist(
                                id='group_checkbox_activity',
                                options=[
                                    {'label': 'Group close toilet motion detected as one visit', 'value': 'group'}],
                                values=[],
                            )
                        ], className='col-md-12 text-center')
                    ], className='row'),
                    html.Div([
                        html.Div(id='location_output', className='col-md-12')
                    ], className='row')
                ], id='activity_graph', className='container-fluid'),
                html.Div([
                    html.Div([
                        html.H3('View resident\'s toilet usage numbers')
                    ], className='row'),
                    html.Div([
                        html.Div([
                            dcc.Dropdown(
                                id='resident_input_toilet_numbers',
                                options=[{'label': i, 'value': i} for i in input_data.get_residents_options()],
                                placeholder='Select resident(s) to view',
                                value=[],
                                multi=True
                            )
                        ], className='col-md-4'),
                        html.Div([
                            dcc.Dropdown(
                                id='filter_input_toilet_numbers',
                                options=[{'label': i, 'value': j} for i, j in
                                         input_data.get_num_visits_filter_options()],
                                value='None',
                                clearable=False
                            )
                        ], className='col-md-4'),
                        html.Div([
                            dcc.DatePickerRange(
                                id='date_picker_toilet_numbers',
                                min_date_allowed=input_data.input_raw_min_date,
                                max_date_allowed=input_data.input_raw_max_date,
                                start_date=input_data.input_raw_min_date.replace(hour=0, minute=0, second=0,
                                                                                 microsecond=0),
                                # need to truncate the dates here
                                end_date=input_data.input_raw_max_date.replace(hour=0, minute=0, second=0,
                                                                               microsecond=0),
                                # to prevent unconverted data error
                                start_date_placeholder_text='Select start date',
                                end_date_placeholder_text='Select end date',
                                minimum_nights=0
                            )
                        ], className='col-md-4')
                    ], className='row'),
                    html.Div([
                        html.Div([
                            dcc.Checklist(
                                id='offset_checkbox_toilet_numbers',
                                options=[{'label': 'Early mornings to be reported as night of previous date',
                                          'value': 'offset'}],
                                values=[],
                            )
                        ], className='col-md-4 text-center'),
                        html.Div([
                            dcc.Checklist(
                                id='ignore_checkbox_toilet_numbers',
                                options=[{'label': 'Ignore durations shorter than 3 seconds', 'value': 'ignore'}],
                                values=[],
                            )
                        ], className='col-md-4 text-center'),
                        html.Div([
                            dcc.Checklist(
                                id='group_checkbox_toilet_numbers',
                                options=[
                                    {'label': 'Group close toilet motion detected as one visit', 'value': 'group'}],
                                values=[],
                            )
                        ], className='col-md-4 text-center')
                    ], className='row'),
                    html.Div([
                        html.Div([
                            dcc.Checklist(
                                id='seven_checkbox_toilet_numbers',
                                options=[{'label': 'Include 7 day moving average', 'value': 'seven'}],
                                values=['seven'],
                            )
                        ], className='col-md-6 text-center'),
                        html.Div([
                            dcc.Checklist(
                                id='twentyone_checkbox_toilet_numbers',
                                options=[{'label': 'Include 21 day moving average', 'value': 'twentyone'}],
                                values=['twentyone'],
                            )
                        ], className='col-md-6 text-center')
                    ], className='row'),
                    html.Div([
                        html.Div(id='toilet_numbers_output', className='col-md-12')
                    ], className='row')
                ], id='toilet_numbers_graph', className='container-fluid'),
                html.Div([
                    html.Div([
                        html.H3('View resident\'s activity durations')
                    ], className='row'),
                    html.Div([
                        html.Div([
                            dcc.Dropdown(
                                id='resident_input_visit_duration',
                                options=[{'label': i, 'value': i} for i in input_data.get_residents_options()],
                                placeholder='Select resident(s) to view',
                                value=[],
                                multi=True
                            )
                        ], className='col-md-4'),
                        html.Div([
                            dcc.Dropdown(
                                id='location_input_visit_duration',
                                options=[{'label': i, 'value': locationMap[i]} for i in locationMap],
                                placeholder='Select a location to view'
                            )
                        ], className='col-md-4'),
                        html.Div([
                            dcc.DatePickerRange(
                                id='date_picker_visit_duration',
                                min_date_allowed=input_data.input_raw_min_date,
                                max_date_allowed=input_data.input_raw_max_date,
                                start_date=input_data.input_raw_min_date.replace(hour=0, minute=0, second=0,
                                                                                 microsecond=0),
                                # need to truncate the dates here
                                end_date=input_data.input_raw_max_date.replace(hour=0, minute=0, second=0,
                                                                               microsecond=0),
                                # to prevent unconverted data error
                                start_date_placeholder_text='Select start date',
                                end_date_placeholder_text='Select end date',
                                minimum_nights=0
                            )
                        ], className='col-md-4')
                    ], className='row'),
                    html.Div([
                        html.Div(id='visit_duration_output', className='col-md-12')
                    ], className='row')
                ], id='visit_duration_graph', className='container-fluid')
            ], className='col-md-12')
        ], role='main', id='page-content', className='col-md-10 ml-sm-auto col-lg-10')
        # this is where the page content goes
    ], className='row')
], className='container-fluid')
