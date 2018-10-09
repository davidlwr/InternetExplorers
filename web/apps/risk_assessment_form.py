from flask import render_template, Flask, request, flash, Markup, redirect, url_for
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, RadioField, FloatField, SelectField, SelectMultipleField, \
    TextField
from wtforms.fields.html5 import DateField
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import InputRequired
from apps.shift_log_form import resident_query
import flask_login
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from app import app, server, db
from DAOs.risk_assessment_DAO import risk_assessment_DAO
from DAOs import resident_DAO
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
    resident = QuerySelectField(query_factory=resident_query, allow_blank=False, get_label='name')
    # date = DateField('Date', format='%Y-%m', validators=[InputRequired('Please enter date!')], default=datetime.today)
    weight = FloatField('Monthly weight updates (kg)')
    num_falls = SelectField('No. of falls for past 6 months',
                            choices=[(0, '0'), (1, '1'), (2, '2-3'), (3, '>=4')], coerce=int, default=0)
    injury_sustained = SelectField('Injury sustained from falls past 6 months',
                                   choices=[(0, 'None'), (1, 'Minor'), (2, 'Major'), (3, 'Hospitalized')], coerce=int,
                                   default=0)
    medical_conditions = SelectField('Number of Medical Conditions',
                                     choices=[(0, '0'), (1, '1-2'), (2, '3-4'), (3, '>=5')], coerce=int, default=0)
    medication_amount = SelectField('Number of Medications',
                                    choices=[(0, '0'), (1, '1-5'), (2, '6-10'), (3, '>=11')], coerce=int, default=0)

    vision = SelectField('Vision (based on observation)',
                         choices=[(0, 'No impairment (with/ without eye glasses)'),
                                  (1, 'Unable to assess/ Blurring of vision'), (2, '1 side - Unilateral blindness'),
                                  (3, '2 side - Bilateral blindness')], coerce=int, default=0)
    hearing = SelectField('Hearing Ability (based on observation)',
                          choices=[(0, 'No impairment (with/ without hearing aid)'),
                                   (1, 'Unable to assess/ Poor hearing (with/ without hearing aid)'),
                                   (2, '1 side - Unilateral deafness'),
                                   (3, '2 side - Bilateral deafness')], coerce=int, default=0)
    mobility = SelectField('Mobility',
                           choices=[(0, 'Unable to move or transfer'), (1, 'Moves with no gait disturbances'),
                                    (2, 'Moves or transfer with assistance'),
                                    (3, 'Moves with unsteady gait needs full assistance')], coerce=int, default=1)
    pain = SelectField('Pain affecting level of function',
                       choices=[(0, ' No pain'), (1, 'Musculoskeletal/ Joint Pain'),
                                (2, 'Generalized pain (e.g. abdominal, headache, etc.)'),
                                (3, 'Critical Pain in other parts')], coerce=int, default=0)
    dependent = SelectField('Elimination',
                            choices=[(0, 'Totally Dependent'), (1, 'Needs assistance with Toileting'),
                                     (2, 'Frequent toileting habits/ Independent with frequency'),
                                     (3, 'Independent with Incontinence ')], coerce=int, default=2)
    dependency = StringField(
        'If dependency is increasing, please describe what type', render_kw={"placeholder": "E.g. toilet usage assistance, mobility assistance, daily activities, etc. "})
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
            submitted_name = form.resident.data.resident_id
            name_to_show = form.resident.data.name
            submitted_date = request.form.get('year_month')
            submitted_weight = form.weight.data

            submitted_num_falls = form.num_falls.data
            submitted_injury_sustained = form.injury_sustained.data

            submitted_medical_conditions = form.medical_conditions.data
            submitted_medication_amount = form.medication_amount.data

            submitted_normal = request.form.get('normal')
            submitted_confusion = request.form.get('confusion')
            submitted_restlessness = request.form.get('restlessness')
            submitted_agitation = request.form.get('agitation')
            submitted_uncooperative = request.form.get('uncooperative')
            submitted_hallucination = request.form.get('hallucination')
            submitted_drowsy = request.form.get('agitation')
            submitted_otherBehaviours = request.form.get('otherBehaviours')
            submitted_status = int(request.form.get('status'))

            submitted_vision = form.vision.data
            submitted_hearing = form.hearing.data
            submitted_mobility = form.mobility.data

            submitted_pain = form.pain.data
            # submitted_noPain = request.form.get('noPain')
            # submitted_general = request.form.get('general')
            # submitted_joint = request.form.get('joint')
            # submitted_critical = request.form.get('critical')
            submitted_otherPain = request.form.get('otherPain')

            submitted_dependent = form.dependent.data
            submitted_dependency = form.dependency.data

            submitted_medicine = request.form.get('medicine')
            submitted_clothes = request.form.get('clothes')
            submitted_eating = request.form.get('eating')
            submitted_bathing = request.form.get('bathing')
            submitted_walking = request.form.get('walking')
            submitted_toileting = request.form.get('toileting')
            submitted_otherAssistance = request.form.get('otherAssistance')

            riskAssessmentDAO = risk_assessment_DAO()
            # riskAssessment = Risk_assessment(submitted_date, submitted_name, submitted_weight, submitted_normal,
            #                                  submitted_confusion, submitted_restlessness, submitted_agitation,
            #                                  submitted_uncooperative, submitted_hallucination, submitted_drowsy,
            #                                  submitted_otherBehaviours, submitted_medicine, submitted_clothes,
            #                                  submitted_eating, submitted_bathing, submitted_walking,
            #                                  submitted_toileting,
            #                                  submitted_otherAssistance, submitted_noPain, submitted_general,
            #                                  submitted_joint,
            #                                  submitted_critical, submitted_otherPain, submitted_medication_amount,
            #                                  submitted_hearing, submitted_vision,
            #                                  submitted_mobility, submitted_dependent,
            #                                  submitted_dependency)

            submitted_dob = form.resident.data.dob
            # submitted_dob = datetime.strptime(submitted_dob, '%Y-%m-%d')
            today = date.today()

            difference_in_years = relativedelta(today, submitted_dob).years
            if difference_in_years < 60:
                age_score = 0
            elif difference_in_years < 70:
                age_score = 1
            elif difference_in_years < 81:
                age_score = 2
            else:
                age_score = 3

            total_score = age_score + submitted_num_falls + submitted_injury_sustained + submitted_medical_conditions + submitted_medication_amount + submitted_status + submitted_vision + submitted_hearing + submitted_pain + submitted_mobility + submitted_dependent

            riskAssessment = Risk_assessment(submitted_date, submitted_name, submitted_weight, submitted_num_falls,
                                             submitted_injury_sustained, submitted_normal,
                                             submitted_confusion, submitted_restlessness, submitted_agitation,
                                             submitted_uncooperative, submitted_hallucination, submitted_drowsy,
                                             submitted_otherBehaviours, submitted_status, submitted_medicine,
                                             submitted_clothes,
                                             submitted_eating, submitted_bathing, submitted_walking,
                                             submitted_toileting,
                                             submitted_otherAssistance, submitted_pain, submitted_otherPain,
                                             submitted_medication_amount, submitted_medical_conditions,
                                             submitted_hearing, submitted_vision,
                                             submitted_mobility, submitted_dependent,
                                             submitted_dependency, total_score)

            response = 'Risk Assessment for ' + name_to_show + ' on ' + submitted_date + ' has already been recorded. Please enter another date.'

            if total_score == 0:
                current_fall_status = "No"
            elif total_score <= 5:
                current_fall_status = "Low"
            elif total_score <= 14:
                current_fall_status = "Medium"
            else:
                current_fall_status = "High"

            try:
                riskAssessmentDAO.insert_risk_assessment(riskAssessment)
                resident_DAO.update_resident_fall_risk(submitted_name, current_fall_status)
            except:
                flash(response)
                print("error here")
                return render_template('raforms.html', form=form, currentDate=datetime.now().strftime('%Y-%m'))

            response = 'Risk Assessment for ' + name_to_show + ' has been successfully recorded. Click <a href="/admin/risk_assessment" class="alert-link">here</a> to view/edit responses.'
            flash(Markup(response))
            return redirect(url_for('showRiskForm'))
        else:
            print("error here2")
            return render_template('raforms.html', form=form, currentDate=datetime.now().strftime('%Y-%m'))
    else:
        print("error here3")
        return render_template('raforms.html', form=form, currentDate=datetime.now().strftime('%Y-%m'))

# @server.route("/donewithform")
# def processForms():
#     return
