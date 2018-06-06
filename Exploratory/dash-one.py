import dash
import datetime
import pandas_datareader.data as web
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import os
import plotly.graph_objs as go

# specify file parameters
file_folder = '../stbern-20180302-20180523-csv/'
file_name = '2018-03-02-2005-sensor.csv'

# read csv
input_raw_data = pd.read_csv(file_folder + file_name)

# combine all data
for filename in os.listdir(file_folder):
    if filename.endswith('2005-sensor.csv'): # for now just try one resident first
        try:
            temp_df = pd.read_csv(file_folder + filename)
            input_raw_data = pd.concat([input_raw_data, temp_df])
        except:
            print('something wrong with ' + filename)

# convert datetime format
input_raw_data['gw_timestamp'] = pd.to_datetime(input_raw_data['gw_timestamp'], format='%Y-%m-%dT%H:%M:%S')

#convert values to 1 and 0 instead of 255
input_raw_data.loc[:, 'value'].replace(255, 1, inplace=True)

# method to get the relevant columns of data
def get_df(input_location, start_date, end_date):
    relevant_data = input_raw_data.loc[(input_raw_data['device_loc'] == input_location)
            & (input_raw_data['gw_timestamp'] < end_date)
            & (input_raw_data['gw_timestamp'] > start_date), ['device_loc','gw_timestamp', 'value']]
    return relevant_data

# generate array for the different available locations
def get_location_options(data):
    # print('debug: ', end='')
    # print(data['device_loc'].unique().tolist())
    return data['device_loc'].unique().tolist()

# default app object instantiation
app = dash.Dash()

# Bootstrap sample template for css
css_source = ['https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css','https://codepen.io/bricakeld/pen/qKZeGq.css']
for css in css_source:
    app.css.append_css({'external_url': css})

# define page layout
app.layout = html.Div(children=[
    html.Div([
        html.Nav([
            html.Div([
                html.Ul([
                    html.Li([
                        html.A([
                            'Dashboard'
                        ], className = 'nav-link active', href='.')
                    ], className = 'nav-item'),
                    html.Li([
                        html.A([
                            'End-of-Shift Reports'
                        ], className = 'nav-link', href='reports')
                    ], className = 'nav-item')
                ], className = 'nav flex-column')
            ], className = 'sidebar-sticky')
        ], className = 'col-md-2 sidebar'),
        html.Main([
            html.Div([
                html.Div([
                    html.H1('Home Page')
                ], className='row'),
                # dcc.Graph(id='example',
                #         figure = {
                #             'data':[
                #                 {'x':[1,2,3,4,5], 'y':[5,34,2,3,4], 'type':'line', 'name':'example_one'}
                #                 ],
                #             'layout': {
                #                 'title':'Random'
                #             }
                #         }),
                # dcc.Input(id='input1', value='Enter something', type='text'),
                # html.Div(id='output1'),
                # dcc.Input(id='graph_title_input', value='', type='text'),
                # html.Div(id='output2')
                html.Div([
                    html.P('Enter the location you want to view:')
                ], className = 'row'),
                html.Div([
                    html.Div([
                        dcc.Dropdown(
                            id='location_input',
                            options=[{'label': i, 'value': i} for i in get_location_options(input_raw_data)],
                            placeholder='Select a location to view'
                        )
                    ], className = 'col-md-6'),
                    html.Div([
                        dcc.DatePickerRange(
                            id='date_picker',
                            min_date_allowed=input_raw_data['gw_timestamp'].min(),
                            max_date_allowed=input_raw_data['gw_timestamp'].max(),
                            start_date=input_raw_data['gw_timestamp'].min().replace(hour=0, minute=0, second=0, microsecond=0), # need to truncate the dates here
                            end_date=input_raw_data['gw_timestamp'].max().replace(hour=0, minute=0, second=0, microsecond=0), #  to prevent unconverted data error
                            start_date_placeholder_text='Select start date',
                            end_date_placeholder_text='Select end date',
                            minimum_nights=0
                        )
                    ], className = 'col-md-6')
                ], className = 'row'),
                html.Div([
                    html.Div(id='location_output', className = 'col-md-12')
                ], className = 'row')
            ], className = 'col-md-12')
        ], role = 'main', className ='col-md-10 ml-sm-auto col-lg-10 px-4')
    ], className = 'row')
    ], className = 'container-fluid')

# @app.callback(
#     Output(component_id='output1', component_property='children'),
#     [Input(component_id='input1', component_property='value')])
# def update_value(input_received):
#     try:
#         return str(float(input_received) ** 3)
#     except:
#         return "Enter a number!"

# @app.callback(
#     Output(component_id='output2', component_property='children'),
#     [Input(component_id='graph_title_input', component_property='value')])
# def update_title(input_received):
#     try:
#         return dcc.Graph(id='example2',
#                 figure = {
#                     'data':[
#                         {'x':[1,2,3,4,5], 'y':[5,34,2,3,4], 'type':'line', 'name':'example_one'}
#                         ],
#                     'layout': {
#                         'title':input_received
#                     }
#                 })
#     except:
#         return "some error occurred"


@app.callback(
    Output(component_id='location_output', component_property='children'),
    [Input(component_id='location_input', component_property='value'),
     Input('date_picker', 'start_date'),
     Input('date_picker', 'end_date')])
def update_graph(input_location, start_date, end_date):
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
        df = get_df(input_location, start_date, end_date)
        # df = input_raw_data
        return dcc.Graph(id='firstplot',
                figure = {
                    'data':[{
                        'x':df['gw_timestamp'],
                        'y':df['value'],
                        'type':'line',
                        'name':input_location,
                        'line':dict(shape='hv'),
                        'fill':'tozeroy'
                    }],
                    'layout': {
                        'title':'Periods with motion detected',
                        'xaxis':{'range':[start_date, end_date]}
                    }
                })
    except Exception as e:
        print(e)
        return ''


if __name__ == '__main__':
    app.run_server(debug=True)
