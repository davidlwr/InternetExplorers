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
import sys

# internal imports
if __name__ == '__main__':
    sys.path.append(".")
    import input_data
    from app import app, server
    from DAOs import resident_DAO
    from Entities import resident
else:
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
    juvo_date_in_use = datetime.datetime(2018, 8, 12, 22, 34, 12) # TODO: change to current system time once live data is available
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
        r['sleep_alerts'], __, __, __, __, __, __ = input_data.get_nightly_sleep_indicator(int(resident['node_id']), date_in_use)
        r['sleep_tooltip'] = []
        if len(r['sleep_alerts']) == 0:
            r['sleep_tooltip'].append("Normal level of motion during sleep detected")
        else: # NOTE: for future changes
            r['sleep_tooltip'].extend(r['sleep_alerts'])

        r['vitals_alerts'], __, __, __, __ = input_data.get_vital_signs_indicator(resident['node_id'], juvo_date_in_use)
        r['vitals_tooltip'] = []
        if len(r['vitals_alerts']) == 0:
            r['vitals_tooltip'].append("Vital signs from previous week appear to be normal")
        else:
            r['vitals_tooltip'].extend(r['vitals_alerts'])

        # print("DEBUG resident id sleep_alerts", resident['node_id'], r['sleep_alerts'])
        r['alert_highest'] = max(0, len(r['toilet_alerts']), len(r['sleep_alerts']), len(r['vitals_alerts']))
        residents.append(r)
    # return render_template('overview_residents_amanda.html', residents=residents)
    information = {}
    information['num_residents'] = len(resident_DAO.get_list_of_residents(location_filter='STB'))
    num_good_health = 0
    for r_dict in residents:
        if r_dict['alert_highest'] == 0:
            num_good_health += 1
    information['health_percentage'] = num_good_health / information['num_residents'] * 100 # in percentage
    return render_template('overview_residents.html', residents=residents, information=information)

# layer 2 routing
@server.route("/overview/<int:node_id>", methods=['GET', 'POST'])
@flask_login.login_required
def detailedLayerTwoOverviewResidents(node_id):
    try:
        date_in_use = datetime.datetime(2018, 4, 18, 23, 34, 12) # TODO: change to current system time once live data is available
        juvo_date_in_use = datetime.datetime(2018, 8, 12, 23, 34, 12)
        resident = resident_DAO.get_resident_by_id(node_id)
        if resident is None:
            return 'Resident not found<a href="/overview">Go Back</a>'
        # parameters
        resident['para_ratio_threshold'] = input_data.get_para_ratio_threshold()

        # sleep alerts
        resident['sleep_alerts'], resident['average_motion_during_sleep'], resident['average_motion_during_sleep_difference'], resident['average_longest_uninterrupted_sleep'], resident['average_longest_uninterrupted_sleep_difference'], resident['qos_mean'], qos_df = input_data.get_nightly_sleep_indicator(node_id, date_in_use)

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

        ### below for vital signs
        resident['vitals_alerts'], resident['past_week_average_breathing'], resident['previous_weeks_average_breathing'], resident['past_week_average_heart'], resident['previous_weeks_average_heart'] = input_data.get_vital_signs_indicator(node_id, juvo_date_in_use)
        past_week_breathing_df = input_data.retrieve_breathing_rate_info(node_id, juvo_date_in_use + datetime.timedelta(days=-7), juvo_date_in_use)
        # CHECK FOR EMPTY DF
        if isinstance(past_week_breathing_df, str) or past_week_breathing_df.empty:
            print("empty data received")
            # add a dummy entry
            past_week_breathing_df = pd.DataFrame()
            past_week_breathing_df['local_start_time'] = [datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')]
            past_week_breathing_df['breathing_rate'] = [0]
        # print("DEBUG: ", past_week_breath_rates)

        past_week_breathing_df['reading_timestamp'] = pd.to_datetime(past_week_breathing_df['local_start_time'], format='%Y-%m-%dT%H:%M:%SZ')
        past_week_breathing_df['date_only'] = past_week_breathing_df['reading_timestamp'].apply(input_data.date_only)

        breathing_graph_df = past_week_breathing_df.groupby(['date_only'], as_index=False)['breathing_rate'].mean()
        past_week_day_range = pd.date_range(juvo_date_in_use.date() + datetime.timedelta(days=-6), juvo_date_in_use.date(), freq='D')

        # set the date as index to allow for filling in of the days range later (for graph display)
        breathing_graph_df.set_index('date_only', inplace=True)

        try:
            breathing_graph_df = breathing_graph_df.loc[past_week_day_range]
        except KeyError as e:
            pass

        breathing_graph_df.fillna(0, inplace=True)
        breathing_graph_df.reset_index(inplace=True)
        breathing_graph_df.rename(columns={'index':'date_only'}, inplace=True)
        breathing_graph_df['past_week_mean'] = resident['past_week_average_breathing']
        breathing_graph_df['previous_weeks_mean'] = resident['previous_weeks_average_breathing']
        breathing_graph_df['normal_lower_bound_rr'] = input_data.normal_lower_bound_rr
        breathing_graph_df['normal_upper_bound_rr'] = input_data.normal_upper_bound_rr
        # print(breathing_graph_df)

        breathing_rates_graph = dict(
                data=[
                    dict(
                        x = breathing_graph_df['date_only'],
                        y = breathing_graph_df['breathing_rate'],
                        type = 'scatter',
                        mode = 'lines',
                        name = 'last wk daily RR',
                        line = dict(
                            width = 2,
                            color = 'rgb(55, 128, 191)'
                        )
                    ),
                    dict(
                        x = breathing_graph_df['date_only'],
                        y = breathing_graph_df['past_week_mean'],
                        type = 'scatter',
                        mode = 'lines',
                        name = 'last wk avg RR',
                        line = dict(
                            width = 2,
                            color = 'rgba(55, 128, 191, 0.5)'
                        )
                    ),
                    dict(
                        x = breathing_graph_df['date_only'],
                        y = breathing_graph_df['normal_lower_bound_rr'],
                        type = 'scatter',
                        mode = 'lines',
                        name = 'min normal RR',
                        line = dict(
                            width = 2,
                            color = 'rgba(191, 0, 0, 0.5)'
                        )
                    ),
                    dict(
                        x = breathing_graph_df['date_only'],
                        y = breathing_graph_df['normal_upper_bound_rr'],
                        type = 'scatter',
                        mode = 'lines',
                        name = 'max normal RR',
                        line = dict(
                            width = 2,
                            color = 'rgba(191, 0, 0, 0.5)'
                        )
                    ),
                    dict(
                        x = breathing_graph_df['date_only'],
                        y = breathing_graph_df['previous_weeks_mean'],
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
                    title = 'Sleep RR in past week',
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

        breathing_rates_json = json.dumps(breathing_rates_graph,
                cls=plotly.utils.PlotlyJSONEncoder)

        past_week_heartbeat_df = input_data.retrieve_heart_rate_info(node_id, juvo_date_in_use + datetime.timedelta(days=-7), juvo_date_in_use)

        # CHECK FOR EMPTY DF
        if isinstance(past_week_heartbeat_df, str) or past_week_heartbeat_df.empty:
            print("empty data received")
            # add a dummy entry
            past_week_heartbeat_df = pd.DataFrame()
            past_week_heartbeat_df['local_start_time'] = [datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')]
            past_week_heartbeat_df['heart_rate'] = [0]

        past_week_heartbeat_df['reading_timestamp'] = pd.to_datetime(past_week_heartbeat_df['local_start_time'], format='%Y-%m-%dT%H:%M:%SZ')
        past_week_heartbeat_df['date_only'] = past_week_heartbeat_df['reading_timestamp'].apply(input_data.date_only)

        heartbeat_graph_df = past_week_heartbeat_df.groupby(['date_only'], as_index=False)['heart_rate'].mean()
        heartbeat_graph_df.set_index('date_only', inplace=True)

        try:
            heartbeat_graph_df = heartbeat_graph_df.loc[past_week_day_range]
        except KeyError as e:
            pass

        heartbeat_graph_df.fillna(0, inplace=True)
        heartbeat_graph_df.reset_index(inplace=True)
        heartbeat_graph_df.rename(columns={'index':'date_only'}, inplace=True)
        heartbeat_graph_df['past_week_mean'] = resident['past_week_average_heart']
        heartbeat_graph_df['previous_weeks_mean'] = resident['previous_weeks_average_heart']
        heartbeat_graph_df['normal_upper_bound_hb'] = input_data.normal_upper_bound_hb

        # print(heartbeat_graph_df.info())
        # print(heartbeat_graph_df)
        heartbeat_rates_graph = dict(
                data=[
                    dict(
                        x = heartbeat_graph_df['date_only'],
                        y = heartbeat_graph_df['heart_rate'],
                        type = 'scatter',
                        mode = 'lines',
                        name = 'last wk daily pulse rate',
                        line = dict(
                            width = 2,
                            color = 'rgb(55, 128, 191)'
                        )
                    ),
                    dict(
                        x = heartbeat_graph_df['date_only'],
                        y = heartbeat_graph_df['normal_upper_bound_hb'],
                        type = 'scatter',
                        mode = 'lines',
                        name = 'max normal pulse rate',
                        line = dict(
                            width = 2,
                            color = 'rgba(191, 0, 0, 0.5)'
                        )
                    ),
                    dict(
                        x = heartbeat_graph_df['date_only'],
                        y = heartbeat_graph_df['past_week_mean'],
                        type = 'scatter',
                        mode = 'lines',
                        name = 'last wk avg RR',
                        line = dict(
                            width = 2,
                            color = 'rgba(55, 128, 191, 0.5)'
                        )
                    ),
                    dict(
                        x = heartbeat_graph_df['date_only'],
                        y = heartbeat_graph_df['previous_weeks_mean'],
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
                    title = 'Sleep pulse rate in past wk',
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

        heartbeat_rates_json = json.dumps(heartbeat_rates_graph,
                cls=plotly.utils.PlotlyJSONEncoder)

        # other vital sign indicators
        resident['check_out_of_rr_range'] = any('respiratory rate from previous week significantly' in s for s in resident['vitals_alerts'])
        resident['check_out_of_hb_range'] = any('Pulse rate during sleep from previous week significantly higher' in s for s in resident['vitals_alerts'])

        # juvo quality of sleep
        qos_df['past_week_average'] = resident['qos_mean']
        # strip tzinfo from juvo api
        qos_df['date_only'] = qos_df['date_timestamp'].apply(lambda x: datetime.datetime.replace(x, tzinfo=None))
        qos_df.sort_values('date_only', inplace=True)
        # print(qos_df.info())
        # print(qos_df)

        qos_graph = dict(
                data=[
                    dict(
                        x = qos_df['date_only'],
                        y = qos_df['qos'],
                        type = 'scatter',
                        mode = 'lines',
                        name = 'last wk nightly sleep quality',
                        line = dict(
                            width = 2,
                            color = 'rgb(55, 128, 191)'
                        )
                    ),
                    dict(
                        x = qos_df['date_only'],
                        y = qos_df['past_week_average'],
                        type = 'scatter',
                        mode = 'lines',
                        name = 'last wk avg sleep quality',
                        line = dict(
                            width = 2,
                            color = 'rgba(55, 128, 191, 0.5)'
                        )
                    )
                ],
                layout = dict(
                    title = 'Quality of sleep in past wk',
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
                        title = '%',
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

        qos_json = json.dumps(qos_graph,
                cls=plotly.utils.PlotlyJSONEncoder)

        return render_template('overview_layer_two.html', resident=resident,
                night_toilet_MA_graph_json=night_toilet_MA_graph_json, sleeping_motion_graph_json=sleeping_motion_graph_json, uninterrupted_sleep_graph_json=uninterrupted_sleep_graph_json,
                breathing_rates_json=breathing_rates_json, heartbeat_rates_json=heartbeat_rates_json, qos_json=qos_json)
    except Exception as e:
        print(e)
        return "An Error Occurred!"

if __name__ == '__main__':
    detailedLayerTwoOverviewResidents(2005)
    pass
