from flask import render_template, Flask, request, flash, Markup, redirect, url_for
from flask_wtf import Form
from wtforms import PasswordField, SubmitField
from DAOs.user_DAO import user_DAO
from flask_login import current_user
from wtforms.validators import InputRequired, Length
from app import app, server, db
import flask_login


class ChangePasswordForm(Form):
    current_password = PasswordField('Current Password', validators=[InputRequired()])
    new_password = PasswordField('New Password', validators=[InputRequired(), Length(min=8, max=25)])
    confirm_password = PasswordField('Confirm New Password', validators=[InputRequired(), Length(min=8, max=25)])
    submit = SubmitField('Submit')


@server.route("/change_password_form", methods=['GET', 'POST'])
@flask_login.login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        # handle logic here
        authenticate_user = user_DAO.authenticate(current_user.username, form.current_password.data)

        if authenticate_user:
            if form.new_password.data == form.confirm_password.data:
                user_DAO.update_password(current_user.username, form.new_password.data)
                flash('Password successfully changed')
                return redirect(url_for('change_password'))

            # if passwords do not match
            flash('New Password does not match Confirmed Password')
            return render_template('change_password.html', form=form)
        # if wrong username or password
        flash('Invalid password')
        return render_template('change_password.html', form=form)

    # else if fail authentication
    return render_template('change_password.html', form=form)
