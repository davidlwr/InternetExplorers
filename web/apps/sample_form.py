from flask import render_template, Flask, request
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, RadioField, FloatField
from wtforms.fields.html5 import DateField
from wtforms.fields.html5 import IntegerRangeField
from wtforms.validators import InputRequired

from app import app, server


class SampleForm(Form):
    name = StringField('Resident Name', validators=[InputRequired('Resident name is required!')])
    date = DateField('Date', format='%Y-%m-%d', validators=[InputRequired('Please enter date!')])
    falls = RadioField('Number of Slips/Falls of Resident',
                       choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3')], coerce=int)
    near_falls = RadioField('Number of Near Falls',
                            choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3')], coerce=int)
    consumption = RadioField('Food consumption',
                             choices=[('insufficient', 'Insufficient'), ('moderate', 'Moderate'),
                                      ('excessive', 'Excessive')])
    temperature = FloatField('Temperature (°C) taken at 3PM (leave blank if temperature has been taken')
    bp = FloatField('Weekly Blood Pressure Reading (Update only on every Sunday)')
    submit = SubmitField('Submit')


# settle routing
@server.route("/anotherflask", methods=['GET', 'POST'])
def showForms():
    form = SampleForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            # handle submitted data here
            # process form here
            submitted_name = form.name.data
            submitted_date = form.date.data
            submitted_falls = form.falls.data
            submitted_near_falls = form.near_falls.data
            submitted_consumption = form.consumption.data
            default_value = True
            submitted_toilet_visits = request.form.get('toilet_visits', default_value)
            submitted_temperature = form.temperature.data
            submitted_bp = form.bp.data
            print(submitted_name)
            return render_template('sample.html', name=submitted_name, date=submitted_date, falls=submitted_falls,
                                   near_falls=submitted_near_falls, consumption=submitted_consumption,
                                   toilet_visits=submitted_toilet_visits, temperature=submitted_temperature,
                                   bp=submitted_bp)
        else:
            return render_template('anotherflask.html', form=form)
    else:
        return render_template('anotherflask.html', form=form)

# @server.route("/donewithform")
# def processForms():
#     return
