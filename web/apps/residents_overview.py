from flask import render_template, Flask, request, url_for
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, RadioField, FloatField
from wtforms.fields.html5 import DateField
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import InputRequired
import flask_login
import datetime
import plotly
import json
import pandas as pd
# internal imports
from apps import input_data
from app import app, server
from DAOs import resident_DAO
from Entities import resident

# settle routing
@server.route("/overview", methods=['GET', 'POST'])
@server.route("/", methods=['GET', 'POST'])
@flask_login.login_required
def showOverviewResidents():
    '''
    This method prepares all the necessary variables to pass into the html for display
    Each resident will have the following:
    Name ('name'), List of Toilet Alerts ('toilet_alerts'),
            List of Sleep Alerts (WIP), Overall Alert Level ('alert_highest')
    NOTE: jinja templates do not allow for import of python modules, so all calculation will be done here
    '''
    residents_raw = resident_DAO.get_list_of_residents()
    residents = []
    date_in_use = datetime.datetime(2018, 4, 19, 23, 34, 12) # TODO: change to current system time once live data is available
    for resident in residents_raw:
        r = {}
        r['name'] = resident['name']
        r['node_id'] = resident['node_id']

        # settle night toilet usage
        r['toilet_alerts'], __ = input_data.get_nightly_toilet_indicator(int(resident['node_id']), date_in_use)
        r['toilet_tooltip'] = []
        if len(r['toilet_alerts']) == 0:
            r['toilet_tooltip'].append("Night toilet visit numbers appear normal")
        else: # NOTE: right now we just append, but use separate list for tooltips in case of future changes
            r['toilet_tooltip'].extend(r['toilet_alerts'])

        # settle sleep duration
        r['sleep_alerts'], __, __, __, __ = input_data.get_nightly_sleep_indicator(int(resident['node_id']), date_in_use)
        r['sleep_tooltip'] = []
        if len(r['sleep_alerts']) == 0:
            r['sleep_tooltip'].append("Normal level of motion during sleep detected")
        else: # NOTE: for future changes
            r['sleep_tooltip'].extend(r['sleep_alerts'])

        # print("DEBUG resident id sleep_alerts", resident['node_id'], r['sleep_alerts'])
        r['alert_highest'] = max(0, len(r['toilet_alerts']), len(r['sleep_alerts']))
        residents.append(r)
    return render_template('overview_residents.html', residents=residents)

# layer 2 routing
@server.route("/overview/<int:node_id>", methods=['GET', 'POST'])
@flask_login.login_required
def detailedLayerTwoOverviewResidents(node_id):
    date_in_use = datetime.datetime(2018, 4, 19, 23, 34, 12) # TODO: change to current system time once live data is available
    resident = resident_DAO.get_resident_by_id(node_id)
    if resident is None:
        return 'Resident not found<a href="/overview">Go Back</a>'
    # parameters
    resident['para_ratio_threshold'] = input_data.get_para_ratio_threshold()

    # sleep alerts
    resident['sleep_alerts'], resident['average_motion_during_sleep'], resident['average_motion_during_sleep_difference'], resident['average_longest_uninterrupted_sleep'], resident['average_longest_uninterrupted_sleep_difference'] = input_data.get_nightly_sleep_indicator(node_id, date_in_use)

    # toilet alerts
    resident['toilet_alerts'], resident['number_of_night_toilet_usage_in_past_week'] = input_data.get_nightly_toilet_indicator(node_id, date_in_use)
    resident['toilet_night_to_both_ratio'], resident['toilet_night_to_both_std'] = input_data.get_percentage_of_night_toilet_usage(node_id, date_in_use)

    # set indicators  {# NOTE: change identifying text below, if input_data function changes #}
    resident['check_indicator_night_toilet_ratio'] = any('of total daily usage in the past month' in s for s in resident['toilet_alerts'])
    resident['check_indicator_night_toilet_MA'] = any('number of night toilet usage in the last week' in s for s in resident['toilet_alerts'])
    resident['check_indicator_sleep_movements'] = any('movements during sleeping hours' in s for s in resident['sleep_alerts'])
    resident['check_indicator_uninterrupted_sleep'] = any('interval of uninterrupted sleep decreased' in s for s in resident['sleep_alerts'])
    # get required information here and pass to the template
    night_toilet_MA_graph_df = input_data.get_num_visits_by_date(date_in_use + datetime.timedelta(days=-28), date_in_use + datetime.timedelta(days=1), 'm-02', node_id, time_period='Night', offset=True, grouped=True)

    # get 3 weeks stacked average series in a day
    night_toilet_MA_graph_df_past_three = night_toilet_MA_graph_df.head(21)
    night_toilet_MA_graph_df_past_three_average = night_toilet_MA_graph_df_past_three['event'].mean()

    # get past week's average
    night_toilet_MA_graph_df_last_week = night_toilet_MA_graph_df.tail(7)
    night_toilet_MA_graph_df_last_week_average = night_toilet_MA_graph_df_last_week['event'].mean()
    night_toilet_MA_graph_df_last_week['latest_mean'] = night_toilet_MA_graph_df_last_week_average
    night_toilet_MA_graph_df_last_week['past_mean'] = night_toilet_MA_graph_df_past_three_average
    resident['number_of_night_toilet_usage_in_past_week_diff'] = night_toilet_MA_graph_df_last_week_average - night_toilet_MA_graph_df_past_three_average
    # print(night_toilet_MA_graph_df_last_week)
    # print(night_toilet_MA_graph_df_last_week_average)

    night_toilet_MA_graph = dict(
            data=[
                dict(
                    x = night_toilet_MA_graph_df_last_week['gw_date_only'],
                    y = night_toilet_MA_graph_df_last_week['event'],
                    type = 'scatter',
                    mode = 'lines',
                    name = 'last wk no.',
                    line = dict(
                        width = 2,
                        color = 'rgb(55, 128, 191)'
                    )
                ),
                dict(
                    x = night_toilet_MA_graph_df_last_week['gw_date_only'],
                    y = night_toilet_MA_graph_df_last_week['latest_mean'],
                    type = 'scatter',
                    mode = 'lines',
                    name = 'last wk avg',
                    line = dict(
                        width = 2,
                        color = 'rgba(55, 128, 191, .5)'
                    )
                ),
                dict(
                    x = night_toilet_MA_graph_df_last_week['gw_date_only'],
                    y = night_toilet_MA_graph_df_last_week['past_mean'],
                    type = 'scatter',
                    mode = 'lines',
                    name = 'prev 3 wk avg',
                    line = dict(
                        width = 2,
                        color = 'rgb(0, 128, 0)'
                    )
                )
            ],
            layout = dict(
                title = 'Night toilet usage in past week',
                titlefont = dict(
                    size = 14
                ),
                autosize = True,
                height = 200,
                showlegend = False,
                margin = dict(
                    l = 20,
                    r = 20,
                    b = 25,
                    t = 30,
                    pad = 5
                ),
                yaxis = dict(
                    scaleanchor = 'x',
                    scaleratio = 0.5,
                    hoverformat = '.2f'
                ),
                xaxis = dict(
                    title = "Day",
                    tickformat = "%a",
                    showticklabels = True,
                    showline = True
                ),
                displayModeBar = False
            )
        )
    night_toilet_MA_graph_json = json.dumps(night_toilet_MA_graph,
            cls=plotly.utils.PlotlyJSONEncoder)

    # motion during sleep graph
    # get the 7 days
    sleeping_motion_df = pd.DataFrame()
    sleeping_motion_df['gw_date_only'] = night_toilet_MA_graph_df_last_week['gw_date_only']
    sleeping_motion_df['values'] = sleeping_motion_df.apply(lambda row: (input_data.motion_duration_during_sleep(
            node_id, row['gw_date_only'], row['gw_date_only'] + datetime.timedelta(days=1))) / 60, axis=1)

    # print(sleeping_motion_df)

    sleeping_motion_df['latest_mean'] = resident['average_motion_during_sleep'] / 60
    sleeping_motion_df['past_mean'] = (resident['average_motion_during_sleep'] - resident['average_motion_during_sleep_difference']) / 60

    sleeping_motion_graph = dict(
            data=[
                dict(
                    x = sleeping_motion_df['gw_date_only'],
                    y = sleeping_motion_df['values'],
                    type = 'scatter',
                    mode = 'lines',
                    name = 'last wk duration',
                    line = dict(
                        width = 2,
                        color = 'rgb(55, 128, 191)'
                    )
                ),
                dict(
                    x = sleeping_motion_df['gw_date_only'],
                    y = sleeping_motion_df['latest_mean'],
                    type = 'scatter',
                    mode = 'lines',
                    name = 'last wk avg',
                    line = dict(
                        width = 2,
                        color = 'rgba(55, 128, 191, .5)'
                    )
                ),
                dict(
                    x = sleeping_motion_df['gw_date_only'],
                    y = sleeping_motion_df['past_mean'],
                    type = 'scatter',
                    mode = 'lines',
                    name = 'prev 3 wk avg',
                    line = dict(
                        width = 2,
                        color = 'rgb(0, 128, 0)'
                    )
                )
            ],
            layout = dict(
                title = 'Sleep motion (mins) in past week',
                titlefont = dict(
                    size = 14
                ),
                autosize = True,
                height = 200,
                showlegend = False,
                margin = dict(
                    l = 25,
                    r = 20,
                    b = 25,
                    t = 30,
                    pad = 5
                ),
                yaxis = dict(
                    scaleanchor = 'x',
                    scaleratio = 0.5,
                    hoverformat = '.2f'
                ),
                xaxis = dict(
                    title = "Day",
                    tickformat = "%a",
                    showticklabels = True,
                    showline = True
                ),
                displayModeBar = False
            )
    )

    sleeping_motion_graph_json = json.dumps(sleeping_motion_graph,
            cls=plotly.utils.PlotlyJSONEncoder)

    # another graph for longest uninterrupted sleep duration
    uninterrupted_sleep_df = pd.DataFrame()
    uninterrupted_sleep_df['gw_date_only'] = night_toilet_MA_graph_df_last_week['gw_date_only']
    uninterrupted_sleep_df['values'] = uninterrupted_sleep_df.apply(lambda row: (input_data.get_average_longest_sleep(
            node_id, row['gw_date_only'], row['gw_date_only'] + datetime.timedelta(days=1))) / 3600, axis=1)

    uninterrupted_sleep_df['latest_mean'] = resident['average_longest_uninterrupted_sleep'] / 3600
    uninterrupted_sleep_df['past_mean'] = (resident['average_longest_uninterrupted_sleep'] - resident['average_longest_uninterrupted_sleep_difference']) / 3600

    uninterrupted_sleep_graph = dict(
            data=[
                dict(
                    x = uninterrupted_sleep_df['gw_date_only'],
                    y = uninterrupted_sleep_df['values'],
                    type = 'scatter',
                    mode = 'lines',
                    name = 'last wk duration',
                    line = dict(
                        width = 2,
                        color = 'rgb(55, 128, 191)'
                    )
                ),
                dict(
                    x = uninterrupted_sleep_df['gw_date_only'],
                    y = uninterrupted_sleep_df['latest_mean'],
                    type = 'scatter',
                    mode = 'lines',
                    name = 'last wk avg',
                    line = dict(
                        width = 2,
                        color = 'rgba(55, 128, 191, .5)'
                    )
                ),
                dict(
                    x = uninterrupted_sleep_df['gw_date_only'],
                    y = uninterrupted_sleep_df['past_mean'],
                    type = 'scatter',
                    mode = 'lines',
                    name = 'prev 3 wk avg',
                    line = dict(
                        width = 2,
                        color = 'rgb(0, 128, 0)'
                    )
                )
            ],
            layout = dict(
                title = 'Uninterrupted slp (hrs) in past wk',
                titlefont = dict(
                    size = 14
                ),
                autosize = True,
                height = 200,
                showlegend = False,
                margin = dict(
                    l = 25,
                    r = 20,
                    b = 25,
                    t = 30,
                    pad = 5
                ),
                yaxis = dict(
                    scaleanchor = 'x',
                    scaleratio = 0.5,
                    hoverformat = '.2f'
                ),
                xaxis = dict(
                    title = "Day",
                    tickformat = "%a",
                    showticklabels = True,
                    showline = True
                ),
                displayModeBar = False
            )
    )

    uninterrupted_sleep_graph_json = json.dumps(uninterrupted_sleep_graph,
            cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('overview_layer_two.html', resident=resident,
            night_toilet_MA_graph_json=night_toilet_MA_graph_json, sleeping_motion_graph_json=sleeping_motion_graph_json, uninterrupted_sleep_graph_json=uninterrupted_sleep_graph_json)
