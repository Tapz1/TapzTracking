# library for the modules required

import os
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, send_from_directory, Response

from itsdangerous import URLSafeTimedSerializer
#from gen_token import generate_confirmation_token, confirm_token
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from threading import Timer
from submissionForms import RegisterForm, TimeEntry_Form, ViewTime_Form, SalesEntryForm, ResetPassword, EditAccount, PayEntryForm
import db_credentials as db
from io import BytesIO#, StringIO # for testing purposes
import csv
from pytz import timezone
