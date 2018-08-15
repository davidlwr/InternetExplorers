import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import datetime

# internal imports
from app import app
from apps import input_data
from DAOs import resident_DAO

locationMap = input_data.get_location_options()

# define page layout

app.layout = html.Div([
    html.Nav([
        html.Div([
            html.Button([
                html.Span('Toggle navigation', className='sr-only'),
                html.Span(className='icon-bar'),
                html.Span(className='icon-bar'),
                html.Span(className='icon-bar')
            ], type='button', className='navbar-toggle'),
            html.A('IE Smart Healthcare', className='navbar-brand', href='/overview')
        ], className='navbar-header'),
        html.Ul([
            # html.Li([
            #     html.A([
            #         html.I(className='fa fa-envelope fa-fw'),
            #         html.I(className='fa fa-caret-down')
            #     ], className='dropdown-toggle', href='#', **{'data-toggle': 'dropdown'}),
            #     html.Ul([
            #         html.Li([
            #             html.A([
            #                 html.Div([
            #                     html.Strong('John Smith'),
            #                     html.Span('Yesterday', className='pull-right text-muted')
            #                 ]),
            #                 html.Div('Lorem ipsum dolor sit amet')
            #             ], href='#')
            #         ]),
            #         html.Li(className='divider'),
            #         html.Li([
            #             html.A([
            #                 html.Strong('Read All Messages'),
            #                 html.I(className='fa fa-angle-right')
            #             ], className='text-center', href='#')
            #         ])
            #     ], className='dropdown-menu dropdown-messages')
            # ], className='dropdown'),
            html.Li([
                html.A([
                    html.I(className='fa fa-user fa-fw'),
                    html.I(className='fa fa-caret-down')
                ], className='dropdown-toggle', href='#', **{'data-toggle': 'dropdown'}),
                html.Ul([
                    # html.Li([
                    #     html.A([
                    #         html.I(className='fa fa-user fa-fw'),
                    #         ' User Profile'
                    #     ], href='#')
                    # ]),
                    # html.Li([
                    #     html.A([
                    #         html.I(className='fa fa-gear fa-fw'),
                    #         ' Settings'
                    #     ], href='#')
                    # ]),
                    # html.Li(className='divider'),
                    html.Li([
                        html.A([
                            html.I(className='fa fa-sign-out fa-fw'),
                            ' Logout'
                        ], href='/logout')
                    ])
                ], className='dropdown-menu dropdown-user')
            ], className='dropdown')
        ], className='nav navbar-top-links navbar-right'),
        html.Div([
            html.Div([
                html.Ul([
                    # html.Li([
                    #     html.Div([
                    #         dcc.Input(placeholder='Search...', type='text', className='form-control'),
                    #         html.Span([
                    #             html.Button([
                    #                 html.I(className='fa fa-search')
                    #             ], className='btn btn-default', type='button')
                    #         ], className='input-group-btn')
                    #     ], className='input-group custom-search-form')
                    # ], className='sidebar-search'),
                    html.Li([
                        html.A([
                            html.I(className='fa fa-dashboard fa-fw'),
                            ' Residents Overview'
                        ], href='/overview')
                    ]),
                    html.Li([
                        html.A([
                            html.I(className='fa fa-chart-o fa-fw'),
                            ' Detailed Charts'
                        ], href='/graphs')
                    ]),
                    html.Li([
                        html.A([
                            html.I(className='fa fa-edit fa-fw'),
                            ' Forms',
                            html.Span(className='fa arrow')
                        ], href='#'),
                        html.Ul([
                            html.Li([
                                html.A('End of Shift Forms', href='/eosforms')
                            ]),
                            html.Li([
                                html.A('Risk Assessment Forms', href='/raforms')
                            ])
                        ], className='nav nav-second-level')
                    ]),
                    html.Li([
                        html.A([
                            html.I(className='fa fa-wrench fa-fw'),
                            ' Manage Users/Residents'
                        ], href='/admin/resident')
                    ])
                ], className='nav', id='side-menu')
            ], className='sidebar-nav navbar-collapse')
        ], className='navbar-default sidebar', role='navigation')
    ], className='navbar navbar-default navbar-static-top', role='navigation', style={'margin-bottom': 0}),
        # sidebar above
        # main body below
    html.Div([
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
                                options=[{'label': resident_DAO.get_resident_name_by_node_id(i), 'value': i} for i in input_data.get_residents_options()],
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
                ], id='activity_graph'),
                html.Div([
                    html.Div([
                        html.H3('View resident\'s toilet usage numbers')
                    ], className='row'),
                    html.Div([
                        html.Div([
                            dcc.Dropdown(
                                id='resident_input_toilet_numbers',
                                options=[{'label': resident_DAO.get_resident_name_by_node_id(i), 'value': i} for i in input_data.get_residents_options()],
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
                ], id='toilet_numbers_graph'),
                html.Div([
                    html.Div([
                        html.H3('View resident\'s activity durations')
                    ], className='row'),
                    html.Div([
                        html.Div([
                            dcc.Dropdown(
                                id='resident_input_visit_duration',
                                options=[{'label': resident_DAO.get_resident_name_by_node_id(i), 'value': i} for i in input_data.get_residents_options()],
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
                ], id='visit_duration_graph')
            ], className='row-fluid')
        ], id='page-wrapper')
        # this is where the page content goes
])


@app.callback(
    Output(component_id='location_output', component_property='children'),
    [Input(component_id='resident_input', component_property='value'),
     Input(component_id='location_input', component_property='value'),
     Input('date_picker', 'start_date'),
     Input('date_picker', 'end_date'),
     Input('group_checkbox_activity', 'values')])
def update_graph_01(input_resident, input_location, start_date, end_date, group_checkbox):
    '''
        Generates graph based on timestamps and whether the latest sensor reading is on or off
        Shaded area indicates detected movement
    '''
    try:
        # add one day to the entered end date as a workaround to allow one day picks (since entered dates are at time 00:00:00)
        temp_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        modified_date = temp_date + datetime.timedelta(days=1)
        end_date = datetime.datetime.strftime(modified_date, '%Y-%m-%d')
        # print('debug ' + str(type(end_date)))
        df = input_data.get_relevant_data(input_location, start_date, end_date, input_resident, grouped=group_checkbox)
        # df = input_data.input_raw_data
        return dcc.Graph(id='firstplot',
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
                         })
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
     Input('twentyone_checkbox_toilet_numbers', 'values')])
def update_graph_02(input_resident, start_date, end_date, filter_input, offset_checkbox, ignore_checkbox,
                    group_checkbox, seven_checkbox, twentyone_checkbox):
    try:
        temp_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        modified_date = temp_date + datetime.timedelta(days=1)
        end_date = datetime.datetime.strftime(modified_date, '%Y-%m-%d')
        draw_data = []
        if filter_input == 'None':  # default option
            for r in input_resident:
                df = input_data.get_num_visits_by_date(start_date, end_date, 'm-02', r,
                                                       ignore_short_durations=ignore_checkbox, grouped=group_checkbox)
                # print("test 2", df)
                draw_data.append({'x': df['gw_date_only'], 'y': df['event'], 'mode': 'lines+markers', 'name': r})
                if seven_checkbox:
                    # get moving averages
                    moving_averages_7 = input_data.get_visit_numbers_moving_average(r, days=7,
                                                                                    ignore_short_durations=ignore_checkbox,
                                                                                    grouped=group_checkbox)

                    # filter relevant dates
                    moving_averages_7 = moving_averages_7.loc[(moving_averages_7['gw_date_only'] < end_date) & (
                            moving_averages_7['gw_date_only'] >= start_date)]
                    draw_data.append({'x': moving_averages_7['gw_date_only'], 'y': moving_averages_7['moving_average'],
                                      'mode': 'lines+markers', 'name': str(r) + ' 7D MA'})
                if twentyone_checkbox:
                    # get moving averages
                    moving_averages_21 = input_data.get_visit_numbers_moving_average(r, days=21,
                                                                                     ignore_short_durations=ignore_checkbox,
                                                                                     grouped=group_checkbox)

                    # filter relevant dates
                    moving_averages_21 = moving_averages_21.loc[(moving_averages_21['gw_date_only'] < end_date) & (
                            moving_averages_21['gw_date_only'] >= start_date)]
                    draw_data.append(
                        {'x': moving_averages_21['gw_date_only'], 'y': moving_averages_21['moving_average'],
                         'mode': 'lines+markers', 'name': str(r) + ' 21D MA'})

        else:
            # if user chose both, both if statements below will execute
            if filter_input != 'Night':  # if not night means have to display for 'Day'
                for r in input_resident:
                    df = input_data.get_num_visits_by_date(start_date, end_date, 'm-02', r, time_period='Day',
                                                           ignore_short_durations=ignore_checkbox,
                                                           grouped=group_checkbox)
                    draw_data.append(
                        {'x': df['gw_date_only'], 'y': df['event'], 'mode': 'lines+markers', 'name': str(r) + ' - Day'})
                    if seven_checkbox:
                        # get moving averages
                        moving_averages_7 = input_data.get_visit_numbers_moving_average(r, days=7, time_period='Day',
                                                                                        ignore_short_durations=ignore_checkbox,
                                                                                        grouped=group_checkbox)

                        # filter relevant dates
                        moving_averages_7 = moving_averages_7.loc[(moving_averages_7['gw_date_only'] < end_date) & (
                                moving_averages_7['gw_date_only'] >= start_date)]
                        draw_data.append(
                            {'x': moving_averages_7['gw_date_only'], 'y': moving_averages_7['moving_average'],
                             'mode': 'lines+markers', 'name': str(r) + ' 7D MA Day'})
                    if twentyone_checkbox:
                        # get moving averages
                        moving_averages_21 = input_data.get_visit_numbers_moving_average(r, days=21, time_period='Day',
                                                                                         ignore_short_durations=ignore_checkbox,
                                                                                         grouped=group_checkbox)

                        # filter relevant dates
                        moving_averages_21 = moving_averages_21.loc[(moving_averages_21['gw_date_only'] < end_date) & (
                                moving_averages_21['gw_date_only'] >= start_date)]
                        draw_data.append(
                            {'x': moving_averages_21['gw_date_only'], 'y': moving_averages_21['moving_average'],
                             'mode': 'lines+markers', 'name': str(r) + ' 21D MA Day'})

            if filter_input != 'Day':  # if not day means have to display for 'Night'
                for r in input_resident:
                    df = input_data.get_num_visits_by_date(start_date, end_date, 'm-02', r, time_period='Night',
                                                           offset=offset_checkbox,
                                                           ignore_short_durations=ignore_checkbox,
                                                           grouped=group_checkbox)  # offset only relevant at night
                    draw_data.append({'x': df['gw_date_only'], 'y': df['event'], 'mode': 'lines+markers',
                                      'name': str(r) + ' - Night'})
                    if seven_checkbox:
                        # get moving averages
                        moving_averages_7 = input_data.get_visit_numbers_moving_average(r, days=7, time_period='Night',
                                                                                        offset=offset_checkbox,
                                                                                        ignore_short_durations=ignore_checkbox,
                                                                                        grouped=group_checkbox)

                        # filter relevant dates
                        moving_averages_7 = moving_averages_7.loc[(moving_averages_7['gw_date_only'] < end_date) & (
                                moving_averages_7['gw_date_only'] >= start_date)]
                        draw_data.append(
                            {'x': moving_averages_7['gw_date_only'], 'y': moving_averages_7['moving_average'],
                             'mode': 'lines+markers', 'name': str(r) + ' 7D MA Night'})
                    if twentyone_checkbox:
                        # get moving averages
                        moving_averages_21 = input_data.get_visit_numbers_moving_average(r, days=21,
                                                                                         time_period='Night',
                                                                                         offset=offset_checkbox,
                                                                                         ignore_short_durations=ignore_checkbox,
                                                                                         grouped=group_checkbox)

                        # filter relevant dates
                        moving_averages_21 = moving_averages_21.loc[(moving_averages_21['gw_date_only'] < end_date) & (
                                moving_averages_21['gw_date_only'] >= start_date)]
                        draw_data.append(
                            {'x': moving_averages_21['gw_date_only'], 'y': moving_averages_21['moving_average'],
                             'mode': 'lines+markers', 'name': str(r) + ' 21D MA Night'})

        return dcc.Graph(id='toilet_numbers_plot',
                         figure={
                             'data': draw_data,
                             'layout': {
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
    except Exception as e:
        print('ERROR: ', end='')
        print(e)
        return ''


@app.callback(
    Output(component_id='visit_duration_output', component_property='children'),
    [Input(component_id='resident_input_visit_duration', component_property='value'),
     Input(component_id='location_input_visit_duration', component_property='value'),
     Input('date_picker_visit_duration', 'start_date'),
     Input('date_picker_visit_duration', 'end_date')])
def update_graph_03(input_resident, input_location, start_date, end_date):
    try:
        temp_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        modified_date = temp_date + datetime.timedelta(days=1)
        end_date = datetime.datetime.strftime(modified_date, '%Y-%m-%d')
        draw_data = []
        for r in input_resident:
            df = input_data.get_visit_duration_and_start_time(start_date, end_date, input_location, r)
            # print(df.head())
            draw_data.append({'x': df['recieved_timestamp'], 'y': df['visit_duration'], 'mode':'markers', 'name': r})
        return dcc.Graph(id = 'visit_duration_plot',
                figure = {
                    'data':draw_data,
                    'layout': {
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
                })
    except Exception as e:
        print('ERROR: ', end='')
        print(e)
        return ''

# next three callbacks automatically updates the resident names live for each graph
@app.callback(
    Output('resident_input', 'options'),
    [Input('resident_input', 'value')])
def set_residents_options_one(selection):
    return [{'label': resident_DAO.get_resident_name_by_node_id(i), 'value': i} for i in input_data.get_residents_options()]

@app.callback(
    Output('resident_input_toilet_numbers', 'options'),
    [Input('resident_input_toilet_numbers', 'value')])
def set_residents_options_one(selection):
    return [{'label': resident_DAO.get_resident_name_by_node_id(i), 'value': i} for i in input_data.get_residents_options()]

@app.callback(
    Output('resident_input_visit_duration', 'options'),
    [Input('resident_input_visit_duration', 'value')])
def set_residents_options_one(selection):
    return [{'label': resident_DAO.get_resident_name_by_node_id(i), 'value': i} for i in input_data.get_residents_options()]
