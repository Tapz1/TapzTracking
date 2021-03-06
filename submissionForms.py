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
    group_name = StringField('Group Name')


class ResetPassword(Form):
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message="Passwords don't match!"),
        validators.Length(min=8)
    ])
    confirm = PasswordField('Confirm Password')


class EditAccount(Form):
    fname = StringField('First Name', [validators.Length(min=1)])
    lname = StringField('Last Name', [validators.Length(min=1)])


class TimeEntry_Form(Form):
    date_form = StringField('Date', [validators.Length(min=1)])
    time_in_form = StringField('Time In', [validators.Length(min=1)])
    time_out_form = StringField('Time Out', [validators.Length(min=1)])
    category_form = StringField('Category', [validators.Length(min=1)])


class ViewTime_Form(Form):
    user_lookup = StringField('User ID', [validators.Length(min=1)])
    date_from = StringField('Date From', [validators.Length(min=1)])
    date_to = StringField('Date To', [validators.Length(min=1)])


class SalesEntryForm(Form):
    # date = StringField("Date", [validators.Length(min=1, max=20)])
    vid_unit = StringField("Video", [validators.Length(min=1)])
    hsd_unit = StringField("Internet", [validators.Length(min=1)])
    voice_unit = StringField("Voice", [validators.Length(min=1)])
    xh_unit = StringField("XH", [validators.Length(min=1)])
    mobile_unit = StringField("Mobile", [validators.Length(min=1)])
    revenue = StringField("Revenue", [validators.Length(min=1)])
    chat_id = StringField("Chat ID")
    cust_id = StringField("Cust ID")
    sesh_id = StringField("Session ID")
    comment = StringField("Comments")


class PayEntryForm(Form):
    date = StringField("Date", [validators.Length(min=1)])
    ref_number = StringField("Reference #")
    pay = StringField("Pay", [validators.Length(min=1)])
    category = StringField("Category", [validators.Length(min=1)])
    pay_method = StringField("Payment Method", [validators.Length(min=1)])
