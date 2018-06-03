import dash
import datetime
import pandas_datareader.data as web
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

# specify file parameters
file_folder = '../stbern-20180302-20180523-csv/'
file_name = '2018-03-02-2005-sensor.csv'

# read csv
input_raw_data = pd.read_csv(file_folder+file_name)

# convert datetime format
input_raw_data['gw_timestamp'] = pd.to_datetime(input_raw_data['gw_timestamp'], format='%Y-%m-%dT%H:%M:%S')

#convert values to 1 and 0 instead of 255
input_raw_data.loc[:, 'value'].replace(255, 1, inplace=True)

# method to get the relevant columns of data
def get_df(input_location):
    relevant_data = input_raw_data.loc[input_raw_data['device_loc'] == input_location, ['device_loc','gw_timestamp', 'value']]
    return relevant_data

# default app object instantiation
app = dash.Dash()

# define page layout
app.layout = html.Div(children=[
    html.H1('Test'),
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
    html.P('Enter the location you want to view:'),
    dcc.Input(id='location_input', value='', type='text'),
    html.Div(id='location_output')
    ])

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
    [Input(component_id='location_input', component_property='value')])
def update_graph(input_location):
    '''
        Generates graph based on timestamps and whether the latest sensor reading is on or off
        Shaded area indicates detected movement
    '''
    try:
        df = get_df(input_location)
        # df = input_raw_data
        return dcc.Graph(id='firstplot',
                figure = {
                    'data':[
                        {'x':df['gw_timestamp'], 'y':df['value'], 'type':'line', 'name':input_location, 'line':dict(shape='hv'), 'fill':'tozeroy'}
                        ],
                    'layout': {
                        'title':'Periods with motion detected'
                    }
                })
    except Exception as e:
        print(e)
        return ''


if __name__ == '__main__':
    app.run_server(debug=True)
