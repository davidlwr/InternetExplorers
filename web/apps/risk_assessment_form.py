from flask import render_template, Flask, request
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, RadioField, FloatField, SelectField, SelectMultipleField, \
    TextField
from wtforms.fields.html5 import DateField
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import InputRequired
from apps.shift_log_form import patient_query
import flask_login
from datetime import datetime

from app import app, server, db
from DAOs.risk_assessment_DAO import risk_assessment_DAO
from Entities.risk_assessment import Risk_assessment


# class Patient(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(45))
#     age = db.Column(db.Integer)
#     fall_risk = db.Column(db.String(45))
#     status = db.Column(db.String(45))
#
#
# def patient_query():
#     return Patient.query


class RiskAssessmentForm(Form):
    name = QuerySelectField(query_factory=patient_query, allow_blank=False, get_label='name')
    date = DateField('Date', format='%Y-%m-%d', validators=[InputRequired('Please enter date!')])
    weight = FloatField('Monthly weight updates (kg)')
    medication_amount = RadioField('Number of medication',
                                   choices=[(0, '0'), (1, '1-2'), (2, '3-4'), (3, '>=5')], coerce=int)
    hearing = RadioField('Hearing Ability (based on observation)',
                         choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], coerce=int)
    vision = RadioField('Vision (based on observation)',
                        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], coerce=int)
    mobility = RadioField('Mobility',
                          choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], coerce=int)
    dependent = RadioField('Dependent',
                           choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], coerce=int)
    dependency = TextField(
        'If dependency is increasing, please describe what type (Example, toilet usage assistance, mobility assistance, daily activities, etc). ')
    submit = SubmitField('Submit')


# settle routing
@server.route("/raforms", methods=['GET', 'POST'])
@flask_login.login_required
def showRiskForm():
    form = RiskAssessmentForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            # handle submitted data here
            # process form here
            submitted_name = form.name.data.id
            name_to_show = form.name.data.name
            submitted_date = form.date.data
            submitted_weight = form.weight.data

            submitted_normal = request.form.get('normal')
            submitted_confusion = request.form.get('confusion')
            submitted_restlessness = request.form.get('restlessness')
            submitted_agitation = request.form.get('agitation')
            submitted_uncooperative = request.form.get('uncooperative')
            submitted_hallucination = request.form.get('hallucination')
            submitted_drowsy = request.form.get('agitation')
            submitted_otherBehaviours = request.form.get('otherBehaviours')

            submitted_medicine = request.form.get('medicine')
            submitted_clothes = request.form.get('clothes')
            submitted_eating = request.form.get('eating')
            submitted_bathing = request.form.get('bathing')
            submitted_walking = request.form.get('walking')
            submitted_toileting = request.form.get('toileting')
            submitted_otherAssistance = request.form.get('otherAssistance')

            submitted_noPain = request.form.get('noPain')
            submitted_general = request.form.get('general')
            submitted_joint = request.form.get('joint')
            submitted_critical = request.form.get('critical')
            submitted_otherPain = request.form.get('otherPain')

            submitted_medication_amount = form.medication_amount.data
            submitted_hearing = form.hearing.data
            submitted_vision = form.vision.data
            submitted_mobility = form.mobility.data
            submitted_dependent = form.dependent.data
            submitted_dependency = form.dependency.data

            riskAssessmentDAO = risk_assessment_DAO()
            riskAssessment = Risk_assessment(submitted_date, submitted_name, submitted_weight, submitted_normal,
                                             submitted_confusion, submitted_restlessness, submitted_agitation,
                                             submitted_uncooperative, submitted_hallucination, submitted_drowsy,
                                             submitted_otherBehaviours, submitted_medicine, submitted_clothes,
                                             submitted_eating, submitted_bathing, submitted_walking,
                                             submitted_toileting,
                                             submitted_otherAssistance, submitted_noPain, submitted_general,
                                             submitted_joint,
                                             submitted_critical, submitted_otherPain, submitted_medication_amount,
                                             submitted_hearing, submitted_vision,
                                             submitted_mobility, submitted_dependent,
                                             submitted_dependency)
            riskAssessmentDAO.insert_risk_assessment(riskAssessment)
            return render_template('FormResponse.html', name=name_to_show)
        else:
            return render_template('raforms.html', form=form)
    else:
        return render_template('raforms.html', form=form)

# @server.route("/donewithform")
# def processForms():
#     return
