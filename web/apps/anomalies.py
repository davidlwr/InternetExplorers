from flask import render_template, Flask, request, flash, Markup, redirect, url_for
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, RadioField, FloatField
from wtforms.fields.html5 import DateField
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import InputRequired
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, Event
from datetime import timedelta
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
	from DAOs import anomaly_DAO, resident_DAO
else:
	from apps import input_data
	from app import app, server
	from DAOs import anomaly_DAO, resident_DAO
	
	
class AnomalyForm(Form):

	startDate = DateField('Start Date', format='%Y-%m-%d', validators=[InputRequired('Please enter Start Date!')])
	endDate = DateField('End Date', format='%Y-%m-%d', validators=[InputRequired('Please enter End Date!')])
    # weight = FloatField('Monthly weight updates (kg)')
    # num_falls = SelectField('No. of falls for past 6 months',
                            # choices=[(0, '0'), (1, '1'), (2, '2-3'), (3, '>=4')], coerce=int, default=0)
    # injury_sustained = SelectField('Injury sustained from falls past 6 months',
                                   # choices=[(0, 'None'), (1, 'Minor'), (2, 'Major'), (3, 'Hospitalized')], coerce=int,
                                   # default=0)
    # medical_conditions = SelectField('Number of Medical Conditions',
                                     # choices=[(0, '0'), (1, '1-2'), (2, '3-4'), (3, '>=5')], coerce=int, default=0)
    # medication_amount = SelectField('Number of Medications',
                                    # choices=[(0, '0'), (1, '1-5'), (2, '6-10'), (3, '>=11')], coerce=int, default=0)

    # vision = SelectField('Vision (based on observation)',
                         # choices=[(0, 'No impairment (with/ without eye glasses)'),
                                  # (1, 'Unable to assess/ Blurring of vision'), (2, '1 side - Unilateral blindness'),
                                  # (3, '2 side - Bilateral blindness')], coerce=int, default=0)
    # hearing = SelectField('Hearing Ability (based on observation)',
                          # choices=[(0, 'No impairment (with/ without hearing aid)'),
                                   # (1, 'Unable to assess/ Poor hearing (with/ without hearing aid)'),
                                   # (2, '1 side - Unilateral deafness'),
                                   # (3, '2 side - Bilateral deafness')], coerce=int, default=0)
    # mobility = SelectField('Mobility',
                           # choices=[(0, 'Unable to move or transfer'), (1, 'Moves with no gait disturbances'),
                                    # (2, 'Moves or transfer with assistance'),
                                    # (3, 'Moves with unsteady gait needs full assistance')], coerce=int, default=1)
    # pain = SelectField('Pain affecting level of function',
                       # choices=[(0, ' No pain'), (1, 'Musculoskeletal/ Joint Pain'),
                                # (2, 'Generalized pain (e.g. abdominal, headache, etc.)'),
                                # (3, 'Critical Pain in other parts')], coerce=int, default=0)
    # dependent = SelectField('Elimination',
                            # choices=[(0, 'Totally Dependent'), (1, 'Needs assistance with Toileting'),
                                     # (2, 'Frequent toileting habits/ Independent with frequency'),
                                     # (3, 'Independent with Incontinence ')], coerce=int, default=2)
    # dependency = StringField(
        # 'If dependency is increasing, please describe what type', render_kw={"placeholder": "E.g. toilet usage assistance, mobility assistance, daily activities, etc. "})
	submit = SubmitField('Submit')
	
# settle routing
@server.route("/anomalies", methods=['GET', 'POST'])
@flask_login.login_required
def showOverviewAnomalies():
	form = AnomalyForm()
	if request.method == 'POST':
		if form.validate_on_submit():
			startDate = form.startDate.data
			endDate = form.endDate.data
			anomalies_raw = anomaly_DAO.get_list_of_anomalies(startDate, endDate)
			# print(anomalies_raw)
			

			anomalies = []
			for anomaly in anomalies_raw:
				r = {}
				dateRaw = anomaly['date']
				r['date'] = dateRaw.date()
				r['resident_id'] = anomaly['resident_id']
				r['category'] = anomaly['category']
				r['type'] = anomaly['type']
				r['description'] = anomaly['description']
				r['response'] = anomaly['response']
				residentName = resident_DAO.get_resident_name_by_resident_id(anomaly['resident_id'])
				r['name'] = residentName
				anomalies.append(r)
			print(anomalies)
			return render_template('anomalies.html', form=form, anomalies=anomalies)	
		else:
			print("error here2")
			return render_template('anomalies.html', form=form)
	else:
		print("error here3")
		return render_template('anomalies.html', form=form)

if __name__ == '__main__':
	showOverviewAnomalies()
	pass
