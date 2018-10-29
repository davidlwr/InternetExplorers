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
	from DAOs import resident_DAO, sensor_hist_DAO
	from sensor_mgmt.sensor_mgmt import Sensor_mgmt, JuvoAPI
	from DAOs.sensor_DAO import sensor_DAO
	from Entities import resident
else:
	from apps import input_data
	from app import app, server
	from DAOs import resident_DAO, sensor_hist_DAO
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
	 # RETURN STATUS CODES
	INVALID_SENSOR = -1
	OK             = 0     # Can be OK and LOW_BATT at the same time
	DISCONNECTED   = 1
	LOW_BATT       = 2
	CHECK_WARN     = 3    # Potentially down
   
	
	residents_raw = resident_DAO.get_list_of_residents()
	
	

	residents = []
	noSensorResidents = []
	date_in_use = datetime.datetime.now() # datetime.datetime(2018, 4, 19, 23, 34, 12) # TODO: change to current system time once live data is available
	juvo_date_in_use = datetime.datetime.now() # datetime.datetime(2018, 8, 12, 22, 34, 12) # TODO: change to current system time once live data is available
	for resident in residents_raw:
		r = {}
		r['name'] = resident['name']
		r['node_id'] = resident['node_id']
		residentid = resident_DAO.get_resident_id_by_resident_name(resident['name'])
		uuids = sensor_hist_DAO.get_uuids_by_id(residentid['resident_id']) #listofuuids
		if len(uuids)==0: 
			noSensorResidents.append(r)
		else:
			infoList = []
			downCount = 0
			upCount = 0
			totalCount = 0
			for uuid in uuids:
				
				id = uuid['uuid']
				_status = Sensor_mgmt.get_sensor_status_v2(id, True)
				statusNumList = _status[0]
				batterystatusList = _status[1]
				statusNum = statusNumList[0]
				batterystatus = '-'
				
				if(len(batterystatusList) > 0):
					batterystatus = batterystatusList[0]
				status = ""
				if statusNum == 0: 
					status = "Up"
					upCount += 1
					totalCount +=1
				else: 
					if statusNum == 3:
						status = "Warning"
					else:
						status = "Down"
					downCount += 1
					totalCount +=1
				loc = sensor_DAO.get_location_by_node_id(id)
				location = loc[0]['location']
				rawtype = sensor_DAO.get_type_by_node_id(id)
				type = rawtype[0]['type']
				if status == "Up" and batterystatus == '-' : 
					if location == 'bed':
						batterystatus = "Plugged"
					else: 
						batterystatus = 100
				elif status == "Down" and batterystatus == '-':
					batterystatus = "Unplugged"
				info = (id,type, location, batterystatus, status)
				infoList.append(info)
			r['infoList'] = infoList
			r['downCount'] = downCount
			r['upCount'] = upCount
			r['totalCount'] = totalCount
			residents.append(r)
	return render_template('sensor_mgmt.html', residents = residents, noSensorResidents = noSensorResidents, downCount = downCount)


if __name__ == '__main__':
	showOverviewSensors()
	pass
