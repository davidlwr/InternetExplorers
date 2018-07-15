from flask import render_template, Flask, request
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired

from app import app, server

class SampleForm(Form):
    sample_name = StringField('sample_name', validators=[InputRequired()])
    sample_submit = SubmitField('Submit')

# settle routing
@server.route("/anotherflask", methods=['GET', 'POST'])
def showForms():
    sample_form = SampleForm()
    if request.method == 'POST':
        if sample_form.validate_on_submit():
            # handle submitted data here
            # process form here
            submitted_name = sample_form.sample_name.data
            print(submitted_name)
            return render_template('sample.html', name=submitted_name)
        else:
            return render_template('anotherflask.html', form=sample_form)
    else:
        return render_template('anotherflask.html', form=sample_form)

# @server.route("/donewithform")
# def processForms():
#     return
