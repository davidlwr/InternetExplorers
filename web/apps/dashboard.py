import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, Event
import datetime
from datetime import timedelta
import pandas as pd
import numpy as np

# internal imports
from app import app
from apps import input_data, input_shiftlogs
from DAOs import resident_DAO
from DAOs.sensor_DAO import sensor_DAO
from sensor_mgmt import JuvoAPI, sensor_mgmt

locationMap = input_data.input_data.get_location_options()
data_update_interval  = 10 * 1000
graph_update_interval = 10 * 1000

# define page layout
# TODO: can return the bank plotly graph output after the exception so that the graph is still there
app.layout = html.Div([
    dcc.Interval(id='data-update', interval=data_update_interval),
    html.P(id='data_update_placeholder'),
    # html.Nav([
    #     html.Div([
    #         html.Button([
    #             html.Span('Toggle navigation', className='sr-only'),
    #             html.Span(className='icon-bar'),
    #             html.Span(className='icon-bar'),
    #             html.Span(className='icon-bar')
    #         ], type='button', className='navbar-toggle'),
    #         html.A('IE Smart Healthcare', className='navbar-brand', href='/overview')
    #     ], className='navbar-header'),
    #     html.Ul([
    #         # html.Li([
    #         #     html.A([
    #         #         html.I(className='fa fa-envelope fa-fw'),
    #         #         html.I(className='fa fa-caret-down')
    #         #     ], className='dropdown-toggle', href='#', **{'data-toggle': 'dropdown'}),
    #         #     html.Ul([
    #         #         html.Li([
    #         #             html.A([
    #         #                 html.Div([
    #         #                     html.Strong('John Smith'),
    #         #                     html.Span('Yesterday', className='pull-right text-muted')
    #         #                 ]),
    #         #                 html.Div('Lorem ipsum dolor sit amet')
    #         #             ], href='#')
    #         #         ]),
    #         #         html.Li(className='divider'),
    #         #         html.Li([
    #         #             html.A([
    #         #                 html.Strong('Read All Messages'),
    #         #                 html.I(className='fa fa-angle-right')
    #         #             ], className='text-center', href='#')
    #         #         ])
    #         #     ], className='dropdown-menu dropdown-messages')
    #         # ], className='dropdown'),
    #         html.Li([
    #             html.A([
    #                 html.I(className='fa fa-user fa-fw'),
    #                 html.I(className='fa fa-caret-down')
    #             ], className='dropdown-toggle', href='#', **{'data-toggle': 'dropdown'}),
    #             html.Ul([
    #                 # html.Li([
    #                 #     html.A([
    #                 #         html.I(className='fa fa-user fa-fw'),
    #                 #         ' User Profile'
    #                 #     ], href='#')
    #                 # ]),
    #                 # html.Li([
    #                 #     html.A([
    #                 #         html.I(className='fa fa-gear fa-fw'),
    #                 #         ' Settings'
    #                 #     ], href='#')
    #                 # ]),
    #                 # html.Li(className='divider'),
    #                 html.Li([
    #                     html.A([
    #                         html.I(className='fa fa-sign-out fa-fw'),
    #                         ' Logout'
    #                     ], href='/logout')
    #                 ])
    #             ], className='dropdown-menu dropdown-user')
    #         ], className='dropdown')
    #     ], className='nav navbar-top-links navbar-right'),
    #     html.Div([
    #         html.Div([
    #             html.Ul([
    #                 # html.Li([
    #                 #     html.Div([
    #                 #         dcc.Input(placeholder='Search...', type='text', className='form-control'),
    #                 #         html.Span([
    #                 #             html.Button([
    #                 #                 html.I(className='fa fa-search')
    #                 #             ], className='btn btn-default', type='button')
    #                 #         ], className='input-group-btn')
    #                 #     ], className='input-group custom-search-form')
    #                 # ], className='sidebar-search'),
    #                 html.Li([
    #                     html.A([
    #                         html.I(className='fa fa-dashboard fa-fw'),
    #                         ' Residents Overview'
    #                     ], href='/overview')
    #                 ]),
    #                 html.Li([
    #                     html.A([
    #                         html.I(className='fa fa-chart-o fa-fw'),
    #                         ' Detailed Charts'
    #                     ], href='/graphs')
    #                 ]),
    #                 html.Li([
    #                     html.A([
    #                         html.I(className='fa fa-edit fa-fw'),
    #                         ' Forms',
    #                         html.Span(className='fa arrow')
    #                     ], href='#'),
    #                     html.Ul([
    #                         html.Li([
    #                             html.A('End of Shift Forms', href='/eosforms')
    #                         ]),
    #                         html.Li([
    #                             html.A('Risk Assessment Forms', href='/raforms')
    #                         ])
    #                     ], className='nav nav-second-level')
    #                 ]),
    #                 html.Li([
    #                     html.A([
    #                         html.I(className='fa fa-wrench fa-fw'),
    #                         ' Manage Users/Residents'
    #                     ], href='/admin/resident')
    #                 ])#,
    #                 # html.Li([
    #                 #     html.A([
    #                 #         html.I(className='fa fa-wrench fa-fw'),
    #                 #         ' Sensors Health'
    #                 #     ], href='/sensorsHealth')
    #                 # ])
    #             ], className='nav', id='side-menu')
    #         ], className='sidebar-nav navbar-collapse')
    #     ], className='navbar-default sidebar', role='navigation')
    # ], className='navbar navbar-default navbar-static-top', role='navigation', style={'margin-bottom': 0}),
        # sidebar above
        # main body below
    # html.Div([
            html.Div([
                # html.Div([
                #     html.H1('Detailed Graphs')
                # ], className='row'),
                html.Div([
                    html.Div([
                        html.H3('Resident\'s toilet usage')
                    ], className='row'),
                    html.Div([
                        html.Div([
                            html.B("Residents"),
                            dcc.Dropdown(
                                id='resident_input_toilet_numbers',
                                options=[{'label': resident_DAO.get_resident_name_by_resident_id(i), 'value': i} for i in input_data.input_data.get_residents_options()],
                                placeholder='Select resident(s) to view',
                                value=[input_data.input_data.get_residents_options()[0] if input_data.input_data.get_residents_options() else None],
                                multi=True
                            )
                        ], className='row'),
                        html.Div([
                            html.B("Day/Night Filter"),
                            dcc.Dropdown(
                                id='filter_input_toilet_numbers',
                                options=[{'label': i, 'value': j} for i, j in
                                         input_data.input_data.get_num_visits_filter_options()],
                                value='None',
                                clearable=False
                            )
                        ], className='row'),
                        html.Div([
                            html.B("Date"),
                            html.Br(),
                            dcc.DatePickerRange(
                                id='date_picker_toilet_numbers',
                                min_date_allowed=input_data.input_data.input_raw_min_date,
                                max_date_allowed=input_data.input_data.input_raw_max_date,
                                # start_date=input_data.input_data.input_raw_min_date.replace(hour=0, minute=0, second=0,
                                #                                                  microsecond=0),
                                start_date=input_data.input_data.input_raw_max_date.replace(hour=0, minute=0, second=0,
                                                                               microsecond=0) - timedelta(days=60),
                                # need to truncate the dates here
                                end_date=input_data.input_data.input_raw_max_date.replace(hour=0, minute=0, second=0,
                                                                               microsecond=0),
                                # to prevent unconverted data error
                                start_date_placeholder_text='Select start date',
                                end_date_placeholder_text='Select end date',
                                minimum_nights=0
                            )
                        ], className='row')
                    ], className='col-md-5 col-xs-12'),
                    html.Div([], className='col-md-2 col-xs-12'),
                    html.Div([
                        html.B(html.U("Other options")),
                        html.Div([
                            dcc.Checklist(
                                id='offset_checkbox_toilet_numbers',
                                options=[{'label': 'Early mornings to be reported as night of previous date',
                                          'value': 'offset'}],
                                values=[],
                            )
                        ], className='row'),
                        html.Div([
                            dcc.Checklist(
                                id='ignore_checkbox_toilet_numbers',
                                options=[{'label': 'Ignore durations shorter than 3 seconds', 'value': 'ignore'}],
                                values=[],
                            )
                        ], className='row'),
                        html.Div([
                            dcc.Checklist(
                                id='group_checkbox_toilet_numbers',
                                options=[
                                    {'label': 'Group close toilet motion detected as one visit', 'value': 'group'}],
                                values=[],
                            )
                        ], className='row'),
                        html.Div([
                            dcc.Checklist(
                                id='seven_checkbox_toilet_numbers',
                                options=[{'label': 'Include 7 day moving average (7D MA)', 'value': 'seven'}],
                                values=['seven'],
                            )
                        ], className='row'),
                        html.Div([
                            dcc.Checklist(
                                id='twentyone_checkbox_toilet_numbers',
                                options=[{'label': 'Include 21 day moving average (21D MA)', 'value': 'twentyone'}],
                                values=['twentyone'],
                            )
                        ], className='row')
                    ], className='col-md-5 col-xs-12'),
                    html.Div([
                        html.Div(id='toilet_numbers_output', className='col-md-12')
                    ], className='row')
                ], id='toilet_numbers_graph'),
                html.Hr(),
                html.Div([
                    html.Div([
                        html.H3('Resident\'s activity durations')
                    ], className='row'),
                    html.Div([
                        html.Div([
                            html.B("Residents"),
                            dcc.Dropdown(
                                id='resident_input_visit_duration',
                                options=[{'label': resident_DAO.get_resident_name_by_resident_id(i), 'value': i} for i in input_data.input_data.get_residents_options()],
                                placeholder='Select resident(s) to view',
                                value=[],
                                multi=True
                            )
                        ], className='col-md-4'),
                        html.Div([
                            html.B("Location"),
                            dcc.Dropdown(
                                id='location_input_visit_duration',
                                options=[{'label': i, 'value': locationMap[i]} for i in locationMap],
                                placeholder='Select a location to view'
                            )
                        ], className='col-md-4'),
                        html.Div([
                            html.B("Date"),
                            html.Br(),
                            dcc.DatePickerRange(
                                id='date_picker_visit_duration',
                                min_date_allowed=input_data.input_data.input_raw_min_date,
                                max_date_allowed=input_data.input_data.input_raw_max_date,
                                start_date=input_data.input_data.input_raw_min_date.replace(hour=0, minute=0, second=0,
                                                                                 microsecond=0),
                                # need to truncate the dates here
                                end_date=input_data.input_data.input_raw_max_date.replace(hour=0, minute=0, second=0,
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
                ], id='visit_duration_graph'),
                html.Hr(),
                html.Div([
                    html.Div([
                        html.H3('Resident\'s logs')
                    ], className='row'),
                    html.Div([
                        html.Div([
                            html.B("Residents"),
                            dcc.Dropdown(
                                id='resident_input_logs',
                                options=[{'label': resident_DAO.get_resident_name_by_resident_id(i), 'value': i} for i in input_shiftlogs.get_residents_options()],
                                placeholder='Select resident(s) to view',
                                value=[],
                                multi=True
                            )
                        ], className='col-md-4'),
                        html.Div([
                            html.B("Day/Night Filter"),
                            dcc.Dropdown(
                                id='filter_input_day_night',
                                options=[{'label': i, 'value': j} for i, j in
                                         input_data.input_data.get_num_visits_filter_options()],
                                value='None',
                                clearable=False
                            )
                        ], className='col-md-4'),
                        html.Div([
                            html.B("Shift Log Information"),
                            dcc.Dropdown(
                                id='filter_input_temp_bp_pulse',
                                options=[{'label': i, 'value': j} for i, j in
                                         input_shiftlogs.get_logs_filter_options()],
                                value='temperature',
                                clearable=False
                            )
                        ], className='col-md-4'),
                        html.Div([
                            html.B("Date"),
                            html.Br(),
                            dcc.DatePickerRange(
                                id='date_picker_logs',
                                min_date_allowed=input_shiftlogs.input_raw_min_date,
                                max_date_allowed=input_shiftlogs.input_raw_max_date,
                                start_date=input_shiftlogs.input_raw_min_date.replace(hour=0, minute=0, second=0,
                                                                                 microsecond=0),
                                # need to truncate the dates here
                                end_date=input_shiftlogs.input_raw_max_date.replace(hour=0, minute=0, second=0,
                                                                               microsecond=0),
                                # to prevent unconverted data error
                                start_date_placeholder_text='Select start date',
                                end_date_placeholder_text='Select end date',
                                minimum_nights=0
                            )
                        ], className='col-md-4')
                    ], className='row'),
                    html.Div([
                        html.Div(id='logs_output', className='col-md-12')
                    ], className='row')
                ], id='logs_graph'),
                html.Hr(),
                html.Div([
                    html.Div([
                        html.H3('Resident\'s sleep vital signs')
                    ], className='row'),
                    html.Div([
                        html.Div([
                            html.B("Residents"),
                            dcc.Dropdown(
                                id='resident_input_vital_signs',
                                options=[{'label': resident_DAO.get_resident_name_by_resident_id(i), 'value': i} for i in sensor_DAO.get_juvo_resident_ids()],
                                placeholder='Select resident(s) to view',
                                value=[],
                                multi=True
                            )
                        ], className='col-md-4'),
                        html.Div([
                            html.B("Vital Signs"),
                            dcc.Dropdown(
                                id='vital_sign_selector',
                                options=[{'label': 'Heart Rate', 'value': 'heart_rate'}, {'label': 'Breathing Rate', 'value': 'breathing_rate'}],
                                placeholder='Select vital sign(s) to view',
                                value=[],
                                multi=True
                            )
                        ], className='col-md-4'),
                        html.Div([
                            html.B("Date"),
                            html.Br(),
                            dcc.DatePickerRange(
                                id='date_picker_vital_signs',
                                min_date_allowed=input_data.input_data.input_raw_min_date,
                                max_date_allowed=input_data.input_data.input_raw_max_date,
                                start_date=input_data.input_data.input_raw_min_date.replace(hour=0, minute=0, second=0,
                                                                                 microsecond=0),
                                # need to truncate the dates here
                                end_date=input_data.input_data.input_raw_max_date.replace(hour=0, minute=0, second=0,
                                                                               microsecond=0),
                                # to prevent unconverted data error
                                start_date_placeholder_text='Select start date',
                                end_date_placeholder_text='Select end date',
                                minimum_nights=0
                            )
                        ], className='col-md-4')
                    ], className='row'),
                    html.Div([
                        html.Div(id='vital_signs_output', className='col-md-12')
                    ], className='row')
                ], id='vital_signs_graph'),
                html.Hr(),
                html.Div([
                    html.Div([
                        html.H3('Resident\'s quality of sleep (from juvo)')
                    ], className='row'),
                    html.Div([
                        html.Div([
                            html.B("Residents"),
                            dcc.Dropdown(
                                id='resident_input_qos',
                                options=[{'label': resident_DAO.get_resident_name_by_resident_id(i), 'value': i} for i in sensor_DAO.get_juvo_resident_ids()],
                                placeholder='Select resident(s) to view',
                                value=[],
                                multi=True
                            )
                        ], className='col-md-6'),
                        html.Div([
                            html.B("Date"),
                            html.Br(),
                            dcc.DatePickerRange(
                                id='date_picker_qos',
                                min_date_allowed=input_data.input_data.input_raw_min_date,
                                max_date_allowed=input_data.input_data.input_raw_max_date,
                                start_date=input_data.input_data.input_raw_min_date.replace(hour=0, minute=0, second=0,
                                                                                 microsecond=0),
                                # need to truncate the dates here
                                end_date=input_data.input_data.input_raw_max_date.replace(hour=0, minute=0, second=0,
                                                                               microsecond=0),
                                # to prevent unconverted data error
                                start_date_placeholder_text='Select start date',
                                end_date_placeholder_text='Select end date',
                                minimum_nights=0
                            )
                        ], className='col-md-6')
                    ], className='row'),
                    html.Div([
                        html.Div(id='qos_output', className='col-md-12')
                    ], className='row')
                ], id='qos_graph'),
                html.Hr(),
                html.Div([
                    html.Div([
                        html.H3('Resident\'s activity')
                    ], className='row'),
                    html.Div([
                        html.Div([
                            html.B("Residents"),
                            dcc.Dropdown(
                                id='resident_input',
                                options=[{'label': resident_DAO.get_resident_name_by_resident_id(i), 'value': i} for i in input_data.input_data.get_residents_options()],
                                placeholder='Select a resident to view'
                            )
                        ], className='col-md-4 col-xs-12'),
                        html.Div([
                            html.B("Location"),
                            dcc.Dropdown(
                                id='location_input',
                                options=[{'label': i, 'value': locationMap[i]} for i in locationMap],
                                placeholder='Select a location to view'
                            )
                        ], className='col-md-4 col-xs-12'),
                        html.Div([
                            html.B("Date"),
                            html.Br(),
                            dcc.DatePickerRange(
                                id='date_picker',
                                min_date_allowed=input_data.input_data.input_raw_min_date,
                                max_date_allowed=input_data.input_data.input_raw_max_date,
                                start_date=input_data.input_data.input_raw_min_date.replace(hour=0, minute=0, second=0,
                                                                                 microsecond=0),
                                # need to truncate the dates here
                                end_date=input_data.input_data.input_raw_max_date.replace(hour=0, minute=0, second=0,
                                                                               microsecond=0),
                                # to prevent unconverted data error
                                start_date_placeholder_text='Select start date',
                                end_date_placeholder_text='Select end date',
                                minimum_nights=0
                            )
                        ], className='col-md-4 col-xs-12')
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
                ], id='activity_graph')
            ], className='row-fluid')
        # ])
        # this is where the page content goes
], style={'background-color': '#f1f4f7', 'padding': '15px', 'font-family': '"Montserrat", "Helvetica Neue", Helvetica, Arial, sans-serif'})


@app.callback(
    Output(component_id='location_output', component_property='children'),
    [Input(component_id='resident_input', component_property='value'),
     Input(component_id='location_input', component_property='value'),
     Input('date_picker', 'start_date'),
     Input('date_picker', 'end_date'),
     Input('group_checkbox_activity', 'values')],
    events=[Event('graph-update-01', 'interval')])
def update_graph_01(input_resident, input_location, start_date, end_date, group_checkbox):
    '''
        Generates graph based on timestamps and whether the latest sensor reading is on or off
        Shaded area indicates detected movement
    '''
    # print(f"Update Graph 01, IR:{input_resident} {type(input_resident)}, IL:{input_location} {type(input_location)}")
    try:
        # add one day to the entered end date as a workaround to allow one day picks (since entered dates are at time 00:00:00)
        temp_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        modified_date = temp_date + datetime.timedelta(days=1)
        end_date = datetime.datetime.strftime(modified_date, '%Y-%m-%d')
        # print('debug ' + str(type(end_date)))
        df = pd.DataFrame()
        df['recieved_timestamp'] = []
        df['event'] = []
        if input_location and input_resident:
            df = input_data.input_data.get_relevant_data(input_location, start_date, end_date, input_resident, grouped=group_checkbox)
        # df = input_data.input_raw_data

        ret_divs = []

        if not (input_resident == None and input_location == None):     # Not initial load, load interval counter, begin auto refresh
            # print("\t graph 01 shoving in interval")
            ret_divs.append(dcc.Interval(id='graph-update-01',interval=graph_update_interval))

        ret_divs.append(dcc.Graph(  id='firstplot',
                                    figure={
                                        'data': [{
                                            'x': df['recieved_timestamp'],
                                            'y': df['event'],
                                            'type': 'line',
                                            'name': input_location,
                                            'line': dict(shape='hv'),
                                            'fill': 'tozeroy'
                                        }],
                                        'layout': {
                                            'paper_bgcolor': 'rgba(0,0,0,0)',
                                            'plot_bgcolor': 'rgba(0,0,0,0)',
                                            'title': 'Periods with motion detected',
                                            'xaxis': {
                                                'range': [start_date, end_date],
                                                'title': 'Timestamps'
                                            },
                                            'yaxis': {
                                                'title': 'Motion detected?'
                                            }
                                        }
                                    },
                                    config={
                                        'editable': False,
                                        'displaylogo': False,
                                        'modeBarButtonsToRemove': ['sendDataToCloud', 'toggleSpikelines']
                                    },
                                    animate=True)
                        )
        return ret_divs
    except Exception as e:
        print('ERROR: ', end='')
        print(e)
        return ''


@app.callback(
    Output(component_id='toilet_numbers_output', component_property='children'),
    [Input(component_id='resident_input_toilet_numbers', component_property='value'),
     Input('date_picker_toilet_numbers', 'start_date'),
     Input('date_picker_toilet_numbers', 'end_date'),
     Input('filter_input_toilet_numbers', 'value'),
     Input('offset_checkbox_toilet_numbers', 'values'),  # if incoming list is empty means don't offset
     Input('ignore_checkbox_toilet_numbers', 'values'),
     Input('group_checkbox_toilet_numbers', 'values'),
     Input('seven_checkbox_toilet_numbers', 'values'),
     Input('twentyone_checkbox_toilet_numbers', 'values')],
    events=[Event('graph-update-02', 'interval')])
def update_graph_02(input_resident, start_date, end_date, filter_input, offset_checkbox, ignore_checkbox,
                    group_checkbox, seven_checkbox, twentyone_checkbox):
    # print(f"Update Graph 02, IR:{input_resident} {type(input_resident)}, FI:{filter_input} {type(filter_input)}")
    try:
        temp_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        modified_date = temp_date + datetime.timedelta(days=1)
        end_date = datetime.datetime.strftime(modified_date, '%Y-%m-%d')
        draw_data = []
        if filter_input == 'None':  # default option
            for r in input_resident:
                r_name = resident_DAO.get_resident_name_by_resident_id(r)
                df = input_data.input_data.get_num_visits_by_date(start_date, end_date, 'm-02', r,
                                                       ignore_short_durations=ignore_checkbox, grouped=group_checkbox)
                # print(df)
                draw_data.append({'x': df['gw_date_only'], 'y': df['event'], 'mode': 'lines+markers', 'name': r_name})
                if seven_checkbox:
                    # get moving averages
                    moving_averages_7 = input_data.input_data.get_visit_numbers_moving_average(r, days=7,
                                                                                    ignore_short_durations=ignore_checkbox,
                                                                                    grouped=group_checkbox)

                    # filter relevant dates
                    moving_averages_7 = moving_averages_7.loc[(moving_averages_7['gw_date_only'] < end_date) & (
                            moving_averages_7['gw_date_only'] >= start_date)]

                    # print(moving_averages_7.info())
                    ### remove dc periods
                    sdt = start_date
                    edt = end_date
                    if isinstance(sdt, str):
                        sdt = datetime.datetime.strptime(sdt, "%Y-%m-%d")
                    if isinstance(edt, str):
                        edt = datetime.datetime.strptime(edt, "%Y-%m-%d")

                    try:
                        sdt = start_date.to_pydatetime()
                        edt = end_date.to_pydatetime()
                    except:
                        pass
                    u = sensor_mgmt.Sensor_mgmt.get_toilet_uuid(r)

                    dc_list = None
                    if u:
                        dc_list = sensor_mgmt.Sensor_mgmt.get_down_periods_motion(u, sdt, edt)

                    if dc_list:
                        for dc_period in dc_list:
                            # print(dc_period)
                            moving_averages_7['moving_average'].loc[(moving_averages_7['gw_date_only'] > dc_period[0]) & (moving_averages_7['gw_date_only'] < dc_period[1])] = np.NaN
                    ###
                    # print(moving_averages_7)
                    draw_data.append({'x': moving_averages_7['gw_date_only'], 'y': moving_averages_7['moving_average'],
                                      'mode': 'lines+markers', 'name': r_name + ' 7D MA'})
                if twentyone_checkbox:
                    # get moving averages
                    moving_averages_21 = input_data.input_data.get_visit_numbers_moving_average(r, days=21,
                                                                                     ignore_short_durations=ignore_checkbox,
                                                                                     grouped=group_checkbox)

                    # filter relevant dates
                    moving_averages_21 = moving_averages_21.loc[(moving_averages_21['gw_date_only'] < end_date) & (
                            moving_averages_21['gw_date_only'] >= start_date)]

                    ### remove dc periods
                    sdt = start_date
                    edt = end_date
                    if isinstance(sdt, str):
                        sdt = datetime.datetime.strptime(sdt, "%Y-%m-%d")
                    if isinstance(edt, str):
                        edt = datetime.datetime.strptime(edt, "%Y-%m-%d")

                    try:
                        sdt = start_date.to_pydatetime()
                        edt = end_date.to_pydatetime()
                    except:
                        pass
                    u = sensor_mgmt.Sensor_mgmt.get_toilet_uuid(r)

                    dc_list = None
                    if u:
                        dc_list = sensor_mgmt.Sensor_mgmt.get_down_periods_motion(u, sdt, edt)

                    if dc_list:
                        for dc_period in dc_list:
                            # print(dc_period)
                            moving_averages_21['moving_average'].loc[(moving_averages_21['gw_date_only'] > dc_period[0]) & (moving_averages_21['gw_date_only'] < dc_period[1])] = np.NaN
                    ###
                    draw_data.append(
                        {'x': moving_averages_21['gw_date_only'], 'y': moving_averages_21['moving_average'],
                         'mode': 'lines+markers', 'name': r_name + ' 21D MA'})

        else:
            # if user chose both, both if statements below will execute
            if filter_input != 'Night':  # if not night means have to display for 'Day'
                for r in input_resident:
                    r_name = resident_DAO.get_resident_name_by_resident_id(r)
                    df = input_data.input_data.get_num_visits_by_date(start_date, end_date, 'm-02', r, time_period='Day',
                                                           ignore_short_durations=ignore_checkbox,
                                                           grouped=group_checkbox)
                    draw_data.append(
                        {'x': df['gw_date_only'], 'y': df['event'], 'mode': 'lines+markers', 'name': r_name + ' - Day'})
                    if seven_checkbox:
                        # get moving averages
                        moving_averages_7 = input_data.input_data.get_visit_numbers_moving_average(r, days=7, time_period='Day',
                                                                                        ignore_short_durations=ignore_checkbox,
                                                                                        grouped=group_checkbox)

                        # filter relevant dates
                        moving_averages_7 = moving_averages_7.loc[(moving_averages_7['gw_date_only'] < end_date) & (
                                moving_averages_7['gw_date_only'] >= start_date)]

                        ### remove dc periods
                        sdt = start_date
                        edt = end_date
                        if isinstance(sdt, str):
                            sdt = datetime.datetime.strptime(sdt, "%Y-%m-%d")
                        if isinstance(edt, str):
                            edt = datetime.datetime.strptime(edt, "%Y-%m-%d")

                        try:
                            sdt = start_date.to_pydatetime()
                            edt = end_date.to_pydatetime()
                        except:
                            pass
                        u = sensor_mgmt.Sensor_mgmt.get_toilet_uuid(r)

                        dc_list = None
                        if u:
                            dc_list = sensor_mgmt.Sensor_mgmt.get_down_periods_motion(u, sdt, edt)

                        if dc_list:
                            for dc_period in dc_list:
                                # print(dc_period)
                                moving_averages_7['moving_average'].loc[(moving_averages_7['gw_date_only'] > dc_period[0]) & (moving_averages_7['gw_date_only'] < dc_period[1])] = np.NaN
                        ###
                        draw_data.append(
                            {'x': moving_averages_7['gw_date_only'], 'y': moving_averages_7['moving_average'],
                             'mode': 'lines+markers', 'name': r_name + ' 7D MA Day'})
                    if twentyone_checkbox:
                        # get moving averages
                        moving_averages_21 = input_data.input_data.get_visit_numbers_moving_average(r, days=21, time_period='Day',
                                                                                         ignore_short_durations=ignore_checkbox,
                                                                                         grouped=group_checkbox)

                        # filter relevant dates
                        moving_averages_21 = moving_averages_21.loc[(moving_averages_21['gw_date_only'] < end_date) & (
                                moving_averages_21['gw_date_only'] >= start_date)]

                        ### remove dc periods
                        sdt = start_date
                        edt = end_date
                        if isinstance(sdt, str):
                            sdt = datetime.datetime.strptime(sdt, "%Y-%m-%d")
                        if isinstance(edt, str):
                            edt = datetime.datetime.strptime(edt, "%Y-%m-%d")

                        try:
                            sdt = start_date.to_pydatetime()
                            edt = end_date.to_pydatetime()
                        except:
                            pass
                        u = sensor_mgmt.Sensor_mgmt.get_toilet_uuid(r)

                        dc_list = None
                        if u:
                            dc_list = sensor_mgmt.Sensor_mgmt.get_down_periods_motion(u, sdt, edt)

                        if dc_list:
                            for dc_period in dc_list:
                                # print(dc_period)
                                moving_averages_21['moving_average'].loc[(moving_averages_21['gw_date_only'] > dc_period[0]) & (moving_averages_21['gw_date_only'] < dc_period[1])] = np.NaN
                        ###
                        draw_data.append(
                            {'x': moving_averages_21['gw_date_only'], 'y': moving_averages_21['moving_average'],
                             'mode': 'lines+markers', 'name': r_name + ' 21D MA Day'})

            if filter_input != 'Day':  # if not day means have to display for 'Night'
                for r in input_resident:
                    r_name = resident_DAO.get_resident_name_by_resident_id(r)
                    df = input_data.input_data.get_num_visits_by_date(start_date, end_date, 'm-02', r, time_period='Night',
                                                           offset=offset_checkbox,
                                                           ignore_short_durations=ignore_checkbox,
                                                           grouped=group_checkbox)  # offset only relevant at night
                    draw_data.append({'x': df['gw_date_only'], 'y': df['event'], 'mode': 'lines+markers',
                                      'name': r_name + ' - Night'})
                    if seven_checkbox:
                        # get moving averages
                        moving_averages_7 = input_data.input_data.get_visit_numbers_moving_average(r, days=7, time_period='Night',
                                                                                        offset=offset_checkbox,
                                                                                        ignore_short_durations=ignore_checkbox,
                                                                                        grouped=group_checkbox)

                        # filter relevant dates
                        moving_averages_7 = moving_averages_7.loc[(moving_averages_7['gw_date_only'] < end_date) & (
                                moving_averages_7['gw_date_only'] >= start_date)]

                        ### remove dc periods
                        sdt = start_date
                        edt = end_date
                        if isinstance(sdt, str):
                            sdt = datetime.datetime.strptime(sdt, "%Y-%m-%d")
                        if isinstance(edt, str):
                            edt = datetime.datetime.strptime(edt, "%Y-%m-%d")

                        try:
                            sdt = start_date.to_pydatetime()
                            edt = end_date.to_pydatetime()
                        except:
                            pass
                        u = sensor_mgmt.Sensor_mgmt.get_toilet_uuid(r)

                        dc_list = None
                        if u:
                            dc_list = sensor_mgmt.Sensor_mgmt.get_down_periods_motion(u, sdt, edt)

                        if dc_list:
                            for dc_period in dc_list:
                                # print(dc_period)
                                moving_averages_7['moving_average'].loc[(moving_averages_7['gw_date_only'] > dc_period[0]) & (moving_averages_7['gw_date_only'] < dc_period[1])] = np.NaN
                        ###
                        draw_data.append(
                            {'x': moving_averages_7['gw_date_only'], 'y': moving_averages_7['moving_average'],
                             'mode': 'lines+markers', 'name': r_name + ' 7D MA Night'})
                    if twentyone_checkbox:
                        # get moving averages
                        moving_averages_21 = input_data.input_data.get_visit_numbers_moving_average(r, days=21,
                                                                                         time_period='Night',
                                                                                         offset=offset_checkbox,
                                                                                         ignore_short_durations=ignore_checkbox,
                                                                                         grouped=group_checkbox)

                        # filter relevant dates
                        moving_averages_21 = moving_averages_21.loc[(moving_averages_21['gw_date_only'] < end_date) & (
                                moving_averages_21['gw_date_only'] >= start_date)]

                        ### remove dc periods
                        sdt = start_date
                        edt = end_date
                        if isinstance(sdt, str):
                            sdt = datetime.datetime.strptime(sdt, "%Y-%m-%d")
                        if isinstance(edt, str):
                            edt = datetime.datetime.strptime(edt, "%Y-%m-%d")

                        try:
                            sdt = start_date.to_pydatetime()
                            edt = end_date.to_pydatetime()
                        except:
                            pass
                        u = sensor_mgmt.Sensor_mgmt.get_toilet_uuid(r)

                        dc_list = None
                        if u:
                            dc_list = sensor_mgmt.Sensor_mgmt.get_down_periods_motion(u, sdt, edt)

                        if dc_list:
                            for dc_period in dc_list:
                                # print(dc_period)
                                moving_averages_21['moving_average'].loc[(moving_averages_21['gw_date_only'] > dc_period[0]) & (moving_averages_21['gw_date_only'] < dc_period[1])] = np.NaN
                        ###
                        draw_data.append(
                            {'x': moving_averages_21['gw_date_only'], 'y': moving_averages_21['moving_average'],
                             'mode': 'lines+markers', 'name': r_name + ' 21D MA Night'})

        ret_divs = []
        if not len(input_resident) == 0:     # Not initial load, load interval counter, begin auto refresh
            # print("\t graph 02 shoving in interval")
            ret_divs.append(dcc.Interval(id='graph-update-02',interval=graph_update_interval))

        ret_divs.append(dcc.Graph(id='toilet_numbers_plot',
                                    figure={
                                        'data': draw_data,
                                        'layout': {
                                            'paper_bgcolor': 'rgba(0,0,0,0)',
                                            'plot_bgcolor': 'rgba(0,0,0,0)',
                                            'title': 'Number of toilet visits',
                                            'xaxis': {
                                                'title': 'Date'
                                            },
                                            'yaxis': {
                                                'title': 'Number'
                                            }
                                        }
                                    },
                                    config={
                                        'editable': False,
                                        'displaylogo': False,
                                        'modeBarButtonsToRemove': ['sendDataToCloud', 'toggleSpikelines']
                                    })
                        )
        return ret_divs
                
    except Exception as e:
        print('ERROR: ', end='')
        print(e)
        return ''


@app.callback(
    Output(component_id='visit_duration_output', component_property='children'),
    [Input(component_id='resident_input_visit_duration', component_property='value'),
     Input(component_id='location_input_visit_duration', component_property='value'),
     Input('date_picker_visit_duration', 'start_date'),
     Input('date_picker_visit_duration', 'end_date')],
    events=[Event('graph-update-03', 'interval')])
def update_graph_03(input_resident, input_location, start_date, end_date):
    # print(f"Update Graph 03. IR:{input_resident}, {type(input_resident)} IL:{input_location} {type(input_location)}")
    try:
        temp_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        modified_date = temp_date + datetime.timedelta(days=1)
        end_date = datetime.datetime.strftime(modified_date, '%Y-%m-%d')
        draw_data = []
        for r in input_resident:
            r_name = resident_DAO.get_resident_name_by_resident_id(r)
            if input_location:
                df = input_data.input_data.get_visit_duration_and_start_time(start_date, end_date, input_location, r)
                # print(df.head())
                draw_data.append({'x': df['recieved_timestamp'], 'y': df['visit_duration'], 'mode':'markers', 'name': r_name})

        ret_divs = []
        if not (len(input_resident) == 0 and input_location == None):     # Not initial load, load interval counter, begin auto refresh
            # print("\t graph 03 shoving in interval")
            ret_divs.append(dcc.Interval(id='graph-update-03',interval=graph_update_interval))


        ret_divs.append(dcc.Graph(  id = 'visit_duration_plot',
                                    figure = {
                                        'data':draw_data,
                                        'layout': {
                                            'paper_bgcolor': 'rgba(0,0,0,0)',
                                            'plot_bgcolor': 'rgba(0,0,0,0)',
                                            'title':'Duration of activity of residents',
                                            'xaxis': {
                                                'title': 'Start datetime of visit'
                                            },
                                            'yaxis': {
                                                'title': 'Duration of visit (seconds)'
                                            }
                                        }
                                    },
                                    config={
                                    'editable': False,
                                    'displaylogo': False,
                                    'modeBarButtonsToRemove': ['sendDataToCloud', 'toggleSpikelines']
                                    },
                                    animate=True)
                            )
        return ret_divs
                
    except Exception as e:
        print('ERROR: ', end='')
        print(e)
        return ''


@app.callback(
    Output(component_id='logs_output', component_property='children'),
    [Input(component_id='resident_input_logs', component_property='value'),
     Input('filter_input_day_night', 'value'),
     Input('filter_input_temp_bp_pulse', 'value'),
     Input('date_picker_logs', 'start_date'),
     Input('date_picker_logs', 'end_date')],
    events=[Event('graph-update-04', 'interval')])
def update_graph_04(input_resident, filter_input, filter_type, start_date, end_date):
    # print(f"Update Graph 04. IR:{input_resident} {type(input_resident)}, FI:{filter_input} {type(filter_input)}")
    try:
        temp_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        modified_date = temp_date + datetime.timedelta(days=1)
        end_date = datetime.datetime.strftime(modified_date, '%Y-%m-%d')
        draw_data = []
        if filter_input == 'None':  # default option
            for r in input_resident:
                r_name = resident_DAO.get_resident_name_by_resident_id(r)
                df = input_shiftlogs.get_logs_by_date(start_date, end_date, r)
                if filter_type != 'sys_dia':
                    draw_data.append({'x': df['date_only'], 'y': df[filter_type], 'mode': 'lines+markers', 'name': r_name})
                else:
                    draw_data.append({'x': df['date_only'], 'y': df['systolic_bp'], 'mode': 'lines+markers', 'name': r_name})
                    draw_data.append({'x': df['date_only'], 'y': df['diastolic_bp'], 'mode': 'lines+markers', 'name': r_name})

        else:

            if filter_input != 'Night':  # if not night means have to display for 'Day'
                for r in input_resident:
                    r_name = resident_DAO.get_resident_name_by_resident_id(r)
                    df = input_shiftlogs.get_logs_by_date(start_date, end_date, r, time_period='Day')
                    if filter_type != 'sys_dia':
                        draw_data.append(
                            {'x': df['date_only'], 'y': df[filter_type], 'mode': 'lines+markers', 'name': r_name + ' - Day'})
                    else:
                        draw_data.append(
                            {'x': df['date_only'], 'y': df['systolic_bp'], 'mode': 'lines+markers', 'name': r_name + ' - Day'})
                        draw_data.append(
                            {'x': df['date_only'], 'y': df['diastolic_bp'], 'mode': 'lines+markers', 'name': r_name + ' - Day'})


            if filter_input != 'Day':  # if not day means have to display for 'Night'
                for r in input_resident:
                    r_name = resident_DAO.get_resident_name_by_resident_id(r)
                    df = input_shiftlogs.get_logs_by_date(start_date, end_date, r, time_period='Night')
                    if filter_type != 'sys_dia':
                        draw_data.append({'x': df['date_only'], 'y': df[filter_type], 'mode': 'lines+markers',
                                          'name': r_name + ' - Night'})
                    else:
                        draw_data.append({'x': df['date_only'], 'y': df['systolic_bp'], 'mode': 'lines+markers',
                                          'name': r_name + ' - Night'})
                        draw_data.append({'x': df['date_only'], 'y': df['diastolic_bp'], 'mode': 'lines+markers',
                                          'name': r_name + ' - Night'})

        ret_divs = []
        if not (len(input_resident) == 0 and filter_input == 'None'):     # Not initial load, load interval counter, begin auto refresh
            # print("\t graph 04 shoving in interval")
            ret_divs.append(dcc.Interval(id='graph-update-04',interval=graph_update_interval))

        ret_divs.append(dcc.Graph(  id='logs_plot',
                                    figure={
                                        'data': draw_data,
                                        'layout': {
                                            'paper_bgcolor': 'rgba(0,0,0,0)',
                                            'plot_bgcolor': 'rgba(0,0,0,0)',
                                            'title': 'Shift Logs',
                                            'xaxis': {
                                                'title': 'Date'
                                            },
                                            'yaxis': {
                                                'title': filter_type
                                            }
                                        }
                                    },
                                    config={
                                        'editable': False,
                                        'displaylogo': False,
                                        'modeBarButtonsToRemove': ['sendDataToCloud', 'toggleSpikelines']
                                    },
                                    animate=True))
        return ret_divs
                
    except Exception as e:
        print('ERROR: ', end='')
        print(e)
        return ''


@app.callback(
    Output('vital_signs_output', component_property='children'),
    [Input('resident_input_vital_signs', 'value'),
    Input('vital_sign_selector', 'value'),
    Input('date_picker_vital_signs', 'start_date'),
    Input('date_picker_vital_signs', 'end_date')],
    events=[Event('graph-update-05', 'interval')])
def update_graph_05(input_residents, input_vital_signs, start_date, end_date):
    # print(f"Update Graph 05. IR:{input_residents} {type(input_residents)}, IVS:{input_vital_signs} {type(input_vital_signs)}")
    # NOTE: input_residents here are the node_ids
    try:
        # add one day to the entered end date as a workaround to allow one day picks (since entered dates are at time 00:00:00)
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        temp_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        modified_date = temp_date + datetime.timedelta(days=1)
        end_date = modified_date #datetime.datetime.strftime(modified_date, '%Y-%m-%d')
        draw_data = []
        if 'heart_rate' in input_vital_signs:
            for r in input_residents:
                r_name = resident_DAO.get_resident_name_by_resident_id(r)
                df = input_data.input_data.retrieve_heart_rate_info(r, start_date, end_date)
                if isinstance(df, str):
                    continue
                draw_data.append({'x': df['local_start_time'], 'y': df['heart_rate'], 'mode': 'markers', 'name': r_name + ' ' + 'heart_rate'})
        if 'breathing_rate' in input_vital_signs:
            for r in input_residents:
                r_name = resident_DAO.get_resident_name_by_resident_id(r)
                df = input_data.input_data.retrieve_breathing_rate_info(r, start_date, end_date)
                if isinstance(df, str):
                    continue
                draw_data.append({'x': df['local_start_time'], 'y': df['breathing_rate'], 'mode': 'markers', 'name': r_name + ' ' + 'breathing_rate'})

        ret_divs = []
        if not (len(input_residents) == 0 and len(input_vital_signs) == 0):     # Not initial load, load interval counter, begin auto refresh
            # print("\t graph 05 shoving in interval")
            ret_divs.append(dcc.Interval(id='graph-update-05',interval=graph_update_interval))


        ret_divs.append(dcc.Graph(  id='vital_signs_plot',
                                    figure = {
                                        'data': draw_data,
                                        'layout': {
                                            'paper_bgcolor': 'rgba(0,0,0,0)',
                                            'plot_bgcolor': 'rgba(0,0,0,0)',
                                            'title':'Vital signs information of elderly',
                                            'xaxis': {
                                                'title': 'Start datetime of recorded vitals'
                                            },
                                            'yaxis': {
                                                'title': 'Vitals reading values (/min)'
                                            }
                                        }
                                    },
                                    config={
                                        'editable': False,
                                        'displaylogo': False,
                                        'modeBarButtonsToRemove': ['sendDataToCloud', 'toggleSpikelines']
                                    },
                                    animate=True))

        return ret_divs
    except Exception as e:
        print('ERROR: ', end='')
        print(e)
        return ''


@app.callback(
    Output('qos_output', component_property='children'),
    [Input('resident_input_qos', 'value'),
    Input('date_picker_qos', 'start_date'),
    Input('date_picker_qos', 'end_date')],
    events=[Event('graph-update-06', 'interval')])
def update_graph_06(input_residents, start_date, end_date):
    # print(f"Update Graph 06. IR:{input_residents} {type(input_residents)}")
    try:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        temp_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        modified_date = temp_date + datetime.timedelta(days=1)
        end_date = modified_date #datetime.datetime.strftime(modified_date, '%Y-%m-%d')
        japi = JuvoAPI.JuvoAPI()
        draw_data = []
        for r in input_residents:
            # first get the target (using API for future refactor)
            curr_target = sensor_DAO.get_juvo_target_from_resident_id(r)
            r_name = resident_DAO.get_resident_name_by_resident_id(r)
            tuple_list = japi.get_qos_by_day(curr_target, start_date, end_date)
            try:
                qos_df = pd.DataFrame(list(tuple_list), columns=['date_timestamp', 'qos'])
                draw_data.append({'x': qos_df['date_timestamp'], 'y': qos_df['qos'], 'mode': 'markers', 'name': r_name + ' - qos'})
            except TypeError as e:
                pass # just don't add to draw data

        ret_divs = []
        if not len(input_residents) == 0:     # Not initial load, load interval counter, begin auto refresh
            # print("\t graph 06 shoving in interval")
            ret_divs.append(dcc.Interval(id='graph-update-06',interval=graph_update_interval))


        ret_divs.append(dcc.Graph(  id='qos_plot', 
                                    figure = {
                                        'data': draw_data,
                                        'layout': {
                                            'paper_bgcolor': 'rgba(0,0,0,0)',
                                            'plot_bgcolor': 'rgba(0,0,0,0)',
                                            'title':'Sleep quality information of elderly (Juvo)',
                                            'xaxis': {
                                                'title': 'Date'
                                            },
                                            'yaxis': {
                                                'title': 'Sleep quality (%)'
                                            }
                                        }
                                    },
                                    config={
                                        'editable': False,
                                        'displaylogo': False,
                                        'modeBarButtonsToRemove': ['sendDataToCloud', 'toggleSpikelines']
                                    },
                                    animate=True))

        return ret_divs
    except Exception as e:
        print('ERROR: ', end='')
        print(e)
        return ''


# next callbacks automatically updates the resident names live for each graph
@app.callback(
    Output('resident_input', 'options'),
    [Input('resident_input', 'value')])
def set_residents_options_one(selection):
    return [{'label': resident_DAO.get_resident_name_by_resident_id(i), 'value': i} for i in input_data.input_data.get_residents_options()]

@app.callback(
    Output('resident_input_toilet_numbers', 'options'),
    [Input('resident_input_toilet_numbers', 'value')])
def set_residents_options_two(selection):
    return [{'label': resident_DAO.get_resident_name_by_resident_id(i), 'value': i} for i in input_data.input_data.get_residents_options()]

@app.callback(
    Output('resident_input_visit_duration', 'options'),
    [Input('resident_input_visit_duration', 'value')])
def set_residents_options_three(selection):
    return [{'label': resident_DAO.get_resident_name_by_resident_id(i), 'value': i} for i in input_data.input_data.get_residents_options()]

@app.callback(
    Output('resident_input_logs', 'options'),
    [Input('resident_input_logs', 'value')])
def set_residents_options_four(selection):
    return [{'label': resident_DAO.get_resident_name_by_resident_id(i), 'value': i} for i in input_shiftlogs.get_residents_options()]


@app.callback(
    Output('resident_input_vital_signs', 'options'),
    [Input('resident_input_vital_signs', 'value')])
def set_residents_options_five(selection):
    return [{'label': resident_DAO.get_resident_name_by_resident_id(i), 'value': i} for i in sensor_DAO.get_juvo_resident_ids()]


@app.callback(
    Output('resident_input_qos', 'options'),
    [Input('resident_input_qos', 'value')])
def set_residents_options_six(selection):
    return [{'label': resident_DAO.get_resident_name_by_resident_id(i), 'value': i} for i in sensor_DAO.get_juvo_resident_ids()]


# This callback periodicallu updates the input_data
@app.callback(  Output('data_update_placeholder', 'children'),
                events=[Event('data-update', 'interval')])
def update_input_data_db():
    print("Data Update Interval triggered... Running data update")
    return input_data.input_data.updateInputData()
    