# forms for user input

from project_lib import *


# for registration page
class RegisterForm(Form):
    fname = StringField('First Name', [validators.Length(min=1, max=20)])
    lname = StringField('Last Name', [validators.Length(min=1, max=20)])
    email = StringField('Email', [validators.DataRequired(), validators.Email(message='Must be a valid email address')])
    # group_name = StringField('Group Name (if applicable)', [validators.Length(min=4, max=25)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message="Passwords don't match!"),
        validators.Length(min=8)
    ])
    confirm = PasswordField('Confirm Password')


class ResetPassword(Form):
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message="Passwords don't match!"),
        validators.Length(min=8)
    ])
    confirm = PasswordField('Confirm Password')


class EditAccount(Form):
    fname = StringField('First Name', [validators.Length(min=1, max=20)])
    lname = StringField('Last Name', [validators.Length(min=1, max=20)])


class TimeEntry_Form(Form):
    date_form = StringField('Date', [validators.Length(min=1, max=20)])
    time_in_form = StringField('Time In', [validators.Length(min=1, max=20)])
    time_out_form = StringField('Time Out', [validators.Length(min=1, max=20)])


class ViewTime_Form(Form):
    user_lookup = StringField('User ID', [validators.Length(min=1, max=20)])
    date_from = StringField('Date From', [validators.Length(min=1, max=20)])
    date_to = StringField('Date To', [validators.Length(min=1, max=20)])


class SalesEntryForm(Form):
    # date = StringField("Date", [validators.Length(min=1, max=20)])
    vid_unit = StringField("Video", [validators.Length(min=1, max=20)])
    hsd_unit = StringField("Internet", [validators.Length(min=1, max=20)])
    voice_unit = StringField("Voice", [validators.Length(min=1, max=20)])
    revenue = StringField("Revenue", [validators.Length(min=1, max=20)])
    chat_id = StringField("Chat ID", [validators.Length(min=1, max=100)])
    cust_id = StringField("Cust ID", [validators.Length(min=1, max=100)])
    comment = StringField("Comments", [validators.Length(min=1, max=100)])
