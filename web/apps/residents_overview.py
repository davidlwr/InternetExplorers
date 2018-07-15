import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import flask

# internal imports
from apps import input_data
from app import app

def getLayout():
    return html.Main(['hello'])

# residents_app.layout = residents_overview.getLayout()
layout = getLayout()
