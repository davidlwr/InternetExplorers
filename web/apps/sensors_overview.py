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
	from DAOs import resident_DAO, sensor_DAO
	from sensor_mgmt.sensor_mgmt import Sensor_mgmt, JuvoAPI
	from DAOs.sensor_DAO import sensor_DAO
	from Entities import resident
else:
	from apps import input_data
	from app import app, server
	from DAOs import resident_DAO, sensor_DAO
	from sensor_mgmt.sensor_mgmt import Sensor_mgmt, JuvoAPI
	from DAOs.sensor_DAO import sensor_DAO
	from Entities import resident

# settle routing
@server.route("/sensor_mgmt", methods=['GET', 'POST'])
@flask_login.login_required
def showOverviewSensors():
	'''
	This method prepares all the necessary variables to pass into the html for display
	Each resident will have the following:
	Name ('name'), List of Toilet Alerts ('toilet_alerts'),
			List of Sleep Alerts (WIP), Overall Alert Level ('alert_highest')
	NOTE: jinja templates do not allow for import of python modules, so all calculation will be done here
	'''

   	# Get list of all Active residents
	residents_raw = resident_DAO.get_list_of_residents(filter_active=True)   

	# Get list of sensor ownerships
	ownership_raw = sensor_DAO.get_ownership_hist()

	# Get list of sensor statuss
	senstatus_raw = Sensor_mgmt.get_all_sensor_status_v2(retBatteryLevel=True)

	# Get list of sensors
	sensors_raw   = sensor_DAO.get_sensors()

	# Loop all residents and compile details into lists
	residents = []
	noSensorResidents = []
	for resident in residents_raw:
		r = {'name': resident['name']}

		# Get list of uuid's owned by curr resident
		uuids = []
		for uuid,periods in ownership_raw.items():
			for rid,sdt,edt in periods:
				if edt == None and rid == resident['resident_id']:
					uuids.append(uuid)
					break

		# Split residents into noSensor and sensor?
		if len(uuids)==0: noSensorResidents.append(r)
		else:
			infoList = []
			upCount    = 0
			downCount  = 0
			# Loop each uuid
			for uuid in uuids:

				# Find sensor details
				type     = ""
				location = ""
				for s in [s for s in sensors_raw if s.uuid == uuid]:
					type     = s.type
					location = s.location
					break

				# Find Sensor status 
				for uuid,statuses,battery in [s for s in senstatus_raw if s[0] == uuid]:

					batt_level  = battery[0] if len(battery) == 1 else '-' 
					statusNum   = statuses[0]
					batt_status = statuses[1] if len(statuses) == 2 else None

					# Settle status string
					status = ""
					if statusNum == Sensor_mgmt.OK:           status = "Up"
					elif statusNum == Sensor_mgmt.CHECK_WARN: status = "Warning"
					if batt_status == Sensor_mgmt.LOW_BATT:   status = "Low batt"

					if status == "Up" or status == "Low batt": upCount += 1
					else: downCount += 1

					# Settle battery status string
					batt_status = ""
					if type == "bed sensor":  batt_status = "Plugged"
					elif batt_level == '-': batt_status = "Unplugged"	# Should not ever happen. But just in case
					else: batt_status = batt_level
					
					info = (uuid, type, location, batt_status, status)
					infoList.append(info)
					break

		# After finishing up all residents, compile
		r['infoList']   = infoList
		r['downCount']  = downCount
		r['upCount']    = upCount
		r['totalCount'] = upCount + downCount
		residents.append(r)

	return render_template('sensor_mgmt.html', residents = residents, noSensorResidents = noSensorResidents, downCount = downCount)


if __name__ == '__main__':
	showOverviewSensors()
	pass
