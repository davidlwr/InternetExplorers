from flask import render_template, Flask, request, flash, Markup, redirect, url_for
from app import app, server
from Entities.sensor import Sensor
from DAOs.sensor_DAO import sensor_DAO
import flask_login


# settle routing
@server.route("/sensorsHealth", methods=['GET', 'POST'])
@flask_login.login_required
def showSensorsHealth():
    test = Sensor(1,"jed","bed",None,None,3)
    sensors = sensor_DAO.get_relevant_sensor_info()
    print(test)
    print(sensors)
    return "here"

