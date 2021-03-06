from project_lib import *
import secrets
import mail_credentials as mc
from flask_mail import Mail, Message


app = Flask(__name__)

app.secret_key = secrets.SECRET_KEY

app.config['SECURITY_PASSWORD_SALT'] = secrets.SECURITY_PASSWORD_SALT

# Configure this environment variable via app.yaml
#CLOUD_STORAGE_BUCKET = os.environ['CLOUD_STORAGE_BUCKET']

# Config  MySQL
app.config['MYSQL_UNIX_SOCKET'] = str(db.MYSQL_UNIX_SOCKET)
app.config['MYSQL_HOST'] = str(db.MYSQL_HOST)
app.config['MYSQL_USER'] = str(db.MYSQL_USER)
app.config['MYSQL_PASSWORD'] = str(db.MYSQL_PASSWORD)
app.config['MYSQL_DB'] = str(db.MYSQL_DB)
app.config['MYSQL_CURSORCLASS'] = str(db.MYSQL_CURSORCLASS)

# Flask Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEBUG'] = True
app.config['MAIL_USERNAME'] = mc.USERNAME
app.config['MAIL_PASSWORD'] = mc.PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = mc.USERNAME
app.config['MAIL_MAX_EMAILS'] = None
app.config['MAIL_ASCII_ATTACHMENTS'] = False

# init MYSQL
mysql = MySQL(app)
mail = Mail(app)

#now = datetime.utcnow()
#todays_date = now.strftime("%m/%d/%Y")
#sql_format = now.strftime("%Y-%m-%d")



"""sends email"""
def send_email(email, subject, template):
    msg = Message(
        subject=subject,
        recipients=[email],
        html=template
    )
    mail.send(msg)
    return 'Confirmation Email Has Been Sent!'


def generate_confirmation_token(email):
    """generates unique token"""
    serializer = URLSafeTimedSerializer(app.secret_key)
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(token, expiration=3600):
    """confirms the token sent back"""
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email


# @ signifies a decorator - way to wrap a function and modifying its behavior

class DecoratorWraps():
    """docstring for DecoratorWraps."""


    def comcaster(f):
        """checks if user has 'comcast' in their group_name in DB"""
        @wraps(f)
        def wrap(*args, **kwargs):
            cur = mysql.connection.cursor()
            cur.execute("SELECT email FROM users WHERE group_name = 'comcast' OR group_name = 'Comcast'")
            comcast_list = str(cur.fetchall())
            email = session['email']
            if 'logged_in' in session and (email).lower() in comcast_list:
                return f(*args, **kwargs)
            else:
                flash('Unauthorized User', 'danger')
                return redirect(url_for('dashboard'))
        return wrap


    def check_confirmed(f):
        """prevents user if email hasn't been confirmed"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # checks if confirmed email
            cur = mysql.connection.cursor()
            current_email = session.get("email")
            cur.execute("SELECT confirmed FROM users WHERE email = %s", [current_email])
            data_confirm = cur.fetchone()
            confirmed_email = str(data_confirm['confirmed'])
            if "0" in confirmed_email:  # 0 in Boolean is False, 1 is True
                flash('Please confirm your account!', 'warning')
                return redirect(url_for('unconfirmed'))
            return f(*args, **kwargs)
        return decorated_function


    def authorized(f):
        """checks if user is labeled "Admin" in DB"""
        @wraps(f)
        def wrap(*args, **kwargs):
            cur = mysql.connection.cursor()
            cur.execute("SELECT email FROM users WHERE role_name = 'Admin'")
            admin_list = str(cur.fetchall())
            email = session['email']
            if 'logged_in' in session and (email).lower() in admin_list:
                return f(*args, **kwargs)
            else:
                flash('Unauthorized User', 'danger')
                return redirect(url_for('dashboard'))
        return wrap


    def is_logged_in(f):
        """checks if user logged in"""
        @wraps(f)
        def wrap(*args, **kwargs):
            if 'logged_in' in session:
                return f(*args, **kwargs)
            else:
                flash('Unauthorized, Please login', 'danger')
                return redirect(url_for('login'))
        return wrap


    def only_whenNotLoggedIn(f):
        """only allows access if user isn't logged in"""
        @wraps(f)
        def wrap(*args, **kwargs):
            if 'logged_in' not in session:
                return f(*args, **kwargs)
            else:
                flash("You're already logged in!", 'danger')
                return redirect(url_for('dashboard'))
        return wrap




#def comcaster(f):
    """checks if user has 'comcast' in their group_name in DB"""
    """
    @wraps(f)
    def wrap(*args, **kwargs):
        cur = mysql.connection.cursor()
        cur.execute("SELECT email FROM users WHERE group_name = 'comcast' OR group_name = 'Comcast'")
        comcast_list = str(cur.fetchall())
        email = session['email']
        if 'logged_in' in session and (email).lower() in comcast_list:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized User', 'danger')
            return redirect(url_for('dashboard'))
    return wrap
    """


@app.route("/")
def index():
    return render_template('home.html')


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route('/register', methods=['GET', 'POST'])
@DecoratorWraps.only_whenNotLoggedIn
def register():
    """user registration"""
    form = RegisterForm(request.form)
    fname = form.fname.data
    lname = form.lname.data
    email = form.email.data
    group_name = form.group_name.data
    # Create cursor
    cur = mysql.connection.cursor()


    if request.method == 'POST' and form.validate():
        # checks if email is already used
        cur.execute("SELECT COUNT(*) AS 'count' FROM users WHERE email = %s", [email])
        email_count = cur.fetchone()
        count = int(email_count['count'])
        if count < 1:
            password = sha256_crypt.encrypt(str(form.password.data))

            # Executes the query statement
            cur.execute("INSERT INTO users(fname, lname, email, password, group_name, confirmed) VALUES(%s, %s, %s, %s, %s, False)", (fname, lname, email.lower(), password, group_name))

            # commit to DB
            mysql.connection.commit()

            token = generate_confirmation_token(email)
            confirm_url = url_for('confirm_email', token=token, _external=True)
            html = render_template('confirm_email.html', confirm_url=confirm_url)
            subject = "You're almost done, %s. Confirm your email!" % (fname)
            send_email(email, subject, html)

            # close connection
            cur.close()

            flash('You are now officially registered and can login!', 'success')

            return redirect(url_for('login'))
        else:
            error = 'Email already in use!'
            return render_template('register.html', error=error, form=form)

    return render_template('register.html', form=form, title='Register!')


@app.route('/confirm/<token>')
@DecoratorWraps.is_logged_in
def confirm_email(token):
    cur = mysql.connection.cursor()
    current_email = session.get("email")
    cur.execute("SELECT user_id FROM users WHERE email = %s", [current_email])
    data_userid = cur.fetchone()
    userid_session = str(data_userid['user_id'])
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')

    result = cur.execute("SELECT * FROM users WHERE email = %s", [email])

    if result > 1:
        flash('Account already confirmed! Go ahead and login!', 'success')
    else:
        cur.execute("UPDATE users SET confirmed = True WHERE user_id = %s", [userid_session])
        mysql.connection.commit()
        cur.close()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('account'))


@app.route('/unconfirmed')
@DecoratorWraps.is_logged_in
def unconfirmed():
    return render_template('unconfirmed.html')


@app.route('/resend')
@DecoratorWraps.is_logged_in
def resend_confirmation():
    cur = mysql.connection.cursor()
    current_email = session.get("email")
    cur.execute("SELECT * FROM users WHERE email = %s", [current_email])
    user_data = cur.fetchone()
    fname = str(user_data['fname'])

    token = generate_confirmation_token(current_email)
    confirm_url = url_for('confirm_email', token=token, _external=True)
    html = render_template('confirm_email.html', confirm_url=confirm_url)
    subject = "You're almost done, %s. Confirm your email!" % (fname)
    send_email(current_email, subject, html)
    flash('A new confirmation email has been sent.', 'success')
    return redirect(url_for('unconfirmed'))


@app.route('/login', methods=['GET', 'POST'])
@DecoratorWraps.only_whenNotLoggedIn
def login():
    """user can log into account"""
    cur = mysql.connection.cursor()
    if request.method == 'POST':

        # Get Form Fields
        email = request.form['email']
        password_candidate = request.form['password']

        # Get user by email
        result = cur.execute("SELECT * FROM users WHERE email = %s", [email])


        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['email'] = email
                cur.execute("SELECT email FROM users WHERE role_name = 'Admin'")
                admin_list = str(cur.fetchall())

                if (email).lower() in admin_list:
                    session['Admin'] = True

            # checks if comcast employee
                cur.execute("SELECT email FROM users WHERE group_name = 'comcast' or group_name = 'Comcast'")
                comcast_list = str(cur.fetchall())

                if email in comcast_list:
                    session['Comcaster'] = True

                # checks if confirmed email
                cur.execute("SELECT confirmed FROM users WHERE email = %s", [email])
                data_confirm = cur.fetchone()
                confirmed_email = str(data_confirm['confirmed'])
                if "0" in confirmed_email:
                    return redirect(url_for('unconfirmed'))
                else:
                    flash('You are now logged in', 'success')
                    return redirect(url_for('time_entry'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Account not found'
            return render_template('login.html', error=error)


    return render_template('login.html', title='Login')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    cur = mysql.connection.cursor()
    form = RegisterForm(request.form)

    if request.method == 'POST':
        email = request.form['email']
        cur.execute("SELECT COUNT(*) AS 'count' FROM users WHERE email = %s", [email])
        email_count = cur.fetchone()
        count = int(email_count['count'])
        if count >= 1:
            token = generate_confirmation_token(email)
            reset_url = url_for('reset_password', token=token, _external=True)
            html = render_template('reset_link.html', reset_url=reset_url)
            subject = "Password Reset"
            send_email(email, subject, html)
            flash('Reset link has been sent to your email', 'success')
            return redirect(url_for('forgot_password'))
        else:
            error = 'No account associated with that email!'
            return render_template('forgot_password.html', error=error, form=form)

    return render_template("forgot_password.html", form=form)


@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    cur = mysql.connection.cursor()
    form = ResetPassword(request.form)

    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')

    cur.execute("SELECT user_id FROM users WHERE email = %s", [email])
    data_userid = cur.fetchone()
    userid_session = str(data_userid['user_id'])
    if request.method == 'POST' and form.validate():
        password = sha256_crypt.encrypt(str(form.password.data))
        cur.execute("UPDATE users SET password = %s WHERE user_id = %s", [password, userid_session])
        mysql.connection.commit()
        cur.close()
        flash('You have successfully reset your password!', 'success')
        return redirect(url_for('login'))
    return render_template("reset_password.html", form=form)


@app.route('/account', methods=['GET', 'POST'])
@DecoratorWraps.is_logged_in
def account():
    cur = mysql.connection.cursor()
    current_email = session.get("email")
    cur.execute("SELECT user_id FROM users WHERE email = %s", [current_email])
    data_userid = cur.fetchone()
    userid_session = str(data_userid['user_id'])

    # checks if confirmed email
    cur.execute("SELECT confirmed FROM users WHERE email = %s", [current_email])
    data_confirm = cur.fetchone()
    confirmed_email = str(data_confirm['confirmed'])

    cur.execute("SELECT * FROM users WHERE user_id = %s", [userid_session])
    user_info = list(cur.fetchall())

    return render_template("account.html", table=user_info, confirmed=confirmed_email)


#@app.route('/edit_account/<string:user_id>', methods=['GET', 'POST'])
#@is_logged_in
def edit_account(user_id):
    """work in progress
    when submitting data to be changed, the data reverts back"""
    cur = mysql.connection.cursor()
    form = EditAccount(request.form)


    cur.execute("SELECT * FROM users WHERE user_id = %s", [user_id])
    data = cur.fetchone()

    # populate form fields
    form.fname.data = data['fname']
    form.lname.data = data['lname']
    #form.email.data = data['email']

    if request.method == 'POST' and form.validate():
        fname = str(request.form['fname'])
        lname = str(request.form['lname'])
        #email = request.form['email']
        # execute time info into database
        cur.execute("UPDATE users SET fname=%s, lname=%s WHERE user_id = %s", [fname, lname, user_id])

        # commit to DB
        mysql.connection.commit()
        # close the connection
        cur.close()

        flash("User Info Updated!", 'success')
        print("Data Received!")
        return redirect(url_for('account'))
    return render_template('edit_account.html', form=form)


@app.route('/time_entry', methods=['GET', 'POST'])
@DecoratorWraps.is_logged_in
@DecoratorWraps.check_confirmed
def time_entry():
    """
    user submits their time_entry
    can also make a button to submit a timestamp
    """
    # time categories
    categories = ["Time Worked", "Meeting", "Training", "Overtime", "Holiday"]

    eastern = timezone('US/Eastern')
    now = datetime.now(eastern)
    todays_date = now.strftime("%m/%d/%Y")
    html_date = now.strftime("%Y-%m-%d")
    html_time = now.strftime("%H:%M")

    cur = mysql.connection.cursor()
    form = TimeEntry_Form(request.form)


    current_email = session.get("email")
    # selects corresponding username data from DB
    cur.execute("SELECT fname, lname, user_id FROM users WHERE email = %s", [current_email])
    data = cur.fetchone()
    # stores what was fetched from the SELECT statement into variables
    fname_session = str(data['fname'])
    lname_session = str(data['lname'])
    userid_session = str(data['user_id'])

    cur.execute("SELECT * FROM time_entry WHERE user_id = %s AND Date = CURDATE()", [userid_session])
    user_time_list = list(cur.fetchall())

    total_hours = float(0)

    for row in user_time_list:
        a = row['Time_In']
        b = row['Time_Out']
        time_in = datetime.strptime(a, '%H:%M')
        time_out = datetime.strptime(b, '%H:%M')
        time_diff = float((time_out - time_in).seconds)
        total_hours += (time_diff / 3600)

    if request.method == 'POST' and form.validate():
        date = form.date_form.data
        time_in = form.time_in_form.data
        time_out = form.time_out_form.data
        category = form.category_form.data
        # execute time info into database
        cur.execute("INSERT INTO time_entry(user_id, Date, FirstName, LastName, Time_In, Time_Out, category) VALUES(%s, %s, %s, %s, %s, %s, %s)", (userid_session, date, fname_session, lname_session, time_in, time_out, category))

        # commit to DB
        mysql.connection.commit()
        # close the connection
        cur.close()

        flash("Time entry submitted!", 'success')
        print("Entry Received!")
        return redirect(url_for('time_entry'))
    return render_template('time.html', title='Time Entry', form=form, name_greet=fname_session, date=todays_date, html_date=html_date, html_time=html_time, total_hours=round(total_hours, 2), table=user_time_list, categories=categories)


@app.route('/edit_time/<string:time_id>', methods=['GET', 'POST'])
@DecoratorWraps.is_logged_in
def edit_time(time_id):
    # time categories
    categories = ["Time Worked", "Meeting", "Training", "Overtime", "Holiday"]

    cur = mysql.connection.cursor()
    form = TimeEntry_Form(request.form)

    cur.execute("SELECT DATE_FORMAT(CURDATE(), '%m/%d/%Y') as 'Todays Date' FROM sales_entry")
    data_date = cur.fetchone()
    todays_date = data_date["Todays Date"]

    result = cur.execute("SELECT * FROM time_entry WHERE time_id = %s", [time_id])
    entry = cur.fetchone()

    # populate form fields
    form.date_form.data = entry['Date']
    form.time_in_form.data = entry['Time_In']
    form.time_out_form.data = entry['Time_Out']
    form.category_form.data = entry['category']


    if request.method == 'POST' and form.validate():
        date = request.form['date_form']
        time_in = request.form['time_in_form']
        time_out = request.form['time_out_form']
        category = request.form['category_form']
        # execute time info into database
        cur.execute("UPDATE time_entry SET Date=%s, Time_In=%s, Time_Out=%s, category=%s WHERE time_id = %s", [date, time_in, time_out, category, time_id])

        # commit to DB
        mysql.connection.commit()
        # close the connection
        cur.close()

        flash("Time Entry Updated!", 'success')
        print("Entry Received!")
        return redirect(url_for('time_entry'))
    return render_template('edit_time.html', form=form, date=todays_date, categories=categories)


@app.route('/delete_time/<string:time_id>', methods=['POST'])
@DecoratorWraps.is_logged_in
def delete_time(time_id):
    """deletes time_entry from database"""
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM time_entry WHERE time_id = %s", [time_id])
    mysql.connection.commit()
    cur.close()

    flash('Entry Deleted', 'success')

    return redirect(url_for('time_entry'))


@app.route("/pay_entry", methods=["GET", "POST"])
@DecoratorWraps.is_logged_in
def pay_entry():
    """page to add wages"""
    cur = mysql.connection.cursor()
    eastern = timezone('US/Eastern')
    now = datetime.now(eastern)
    todays_date = now.strftime("%m/%d/%Y")
    html_date = now.strftime("%Y-%m-%d")

    current_email = session.get("email")
    cur.execute("SELECT * FROM users WHERE email = %s", [current_email])
    data = cur.fetchone()
    fname_session = data["fname"]
    lname_session = data["lname"]
    userid_session = data["user_id"]

    form = PayEntryForm(request.form)

    categories = ["Tips", "Payday", "Commission", "Bonus", "Miscellaneous"]
    pay_types = ["Cash", "Credit Card", "Check", "Direct Deposit"]

    cur.execute("SELECT * FROM wages WHERE user_id= %s AND date = CURDATE()", [userid_session])
    pay_data = list(cur.fetchall())

    total_pay = (0)
    for pay in pay_data:
        total_pay += pay["pay"]

    tips_cash_total = 0
    tips_card_total = 0
    payday = 0
    commission = 0
    bonus = 0
    miscellaneous = 0

    for n in pay_data:
        if "Cash" in n["payment_method"] and "Tips" in n["category"]:
            tips_cash_total += n["pay"]
        elif "Credit Card" in n["payment_method"] and "Tips" in n["category"]:
            tips_card_total += n["pay"]
        elif "Payday" in n["category"]:
            payday += n["pay"]
        elif "Commission" in n["category"]:
            commission += n["pay"]
        elif "Bonus" in n["category"]:
            bonus += n["pay"]
        elif "Miscellaneous" in n["category"]:
            miscellaneous += n["pay"]



    if request.method == 'POST' and form.validate():
        if "submit_pay" in request.form:
            date = form.date.data
            ref_number = form.ref_number.data
            pay = form.pay.data
            category = form.category.data
            pay_method = form.pay_method.data
            cur.execute("INSERT INTO wages(date, user_id, fname, lname, ref_number, pay, category, payment_method) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", [date, userid_session, fname_session, lname_session, ref_number, pay, category, pay_method])
            mysql.connection.commit()

            flash("Pay Submitted!", "success")
            return redirect(url_for('pay_entry'))

    cur.close()

    return render_template("pay_entry.html", form=form, name_greet=fname_session, date=todays_date, html_date=html_date, categories=categories, total_pay=total_pay, pay_data=pay_data, pay_types=pay_types, cash_tips=tips_cash_total, card_tips=tips_card_total, payday=payday, commission=commission, bonus=bonus, miscellaneous=miscellaneous)


@app.route("/view_pay", methods=["GET", "POST"])
@DecoratorWraps.is_logged_in
def view_pay():
    cur = mysql.connection.cursor()
    form = ViewTime_Form(request.form)

    eastern = timezone('US/Eastern')
    now = datetime.now(eastern)
    todays_date = now.strftime("%m/%d/%Y")
    html_date = now.strftime("%Y-%m-%d")

    current_email = session.get("email")
    cur.execute("SELECT * FROM users WHERE email = %s", [current_email])
    data = cur.fetchone()
    fname_session = data["fname"]
    lname_session = data["lname"]
    userid_session = data["user_id"]

    total_pay = 0
    tips_cash_total = 0
    tips_card_total = 0
    payday = 0
    commission = 0
    bonus = 0
    miscellaneous = 0

    date_from = form.date_from.data
    date_to = form.date_to.data
    cur.execute("SELECT * FROM wages WHERE user_id = %s AND date >= %s AND date <= %s", [userid_session, date_from, date_to])
    pay_data = list(cur.fetchall())

    for n in pay_data:
        total_pay += n["pay"]
        if "Cash" in n["payment_method"] and "Tips" in n["category"]:
            tips_cash_total += n["pay"]
        elif "Credit Card" in n["payment_method"] and "Tips" in n["category"]:
            tips_card_total += n["pay"]
        elif "Payday" in n["category"]:
            payday += n["pay"]
        elif "Commission" in n["category"]:
            commission += n["pay"]
        elif "Bonus" in n["category"]:
            bonus += n["pay"]
        elif "Miscellaneous" in n["category"]:
            miscellaneous += n["pay"]


    if request.method == 'POST':
        if "search" in request.form:
            return render_template("view_pay.html", pay_data=pay_data, total_pay=total_pay, cash_tips=tips_cash_total, card_tips=tips_card_total, payday=payday, commission=commission, bonus=bonus, miscellaneous=miscellaneous, name_greet=fname_session, date=todays_date)

    cur.close()
    return render_template("view_pay.html", form=form, name_greet=fname_session, html_date=html_date)


@app.route('/delete_pay/<string:pay_id>', methods=['POST'])
@DecoratorWraps.is_logged_in
def delete_pay(pay_id):
    """delete pay by pay_id"""
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM wages WHERE pay_id = %s", [pay_id])
    mysql.connection.commit()
    cur.close()

    flash('Pay Deleted', 'success')

    return redirect(url_for('pay_entry'))


@app.route("/sales_entry", methods=['GET', 'POST'])
@DecoratorWraps.is_logged_in
@DecoratorWraps.check_confirmed
@DecoratorWraps.comcaster
def sales_entry():
    """page to add sales"""
    """Needs similar formatting to time_entry function"""

    cur = mysql.connection.cursor()

    cur.execute("SELECT DATE_FORMAT(CURDATE(), '%m/%d/%Y') as 'Todays Date' FROM sales_entry")
    data_date = cur.fetchone()
    todays_date = data_date["Todays Date"]

    form = SalesEntryForm(request.form)

    current_email = session.get("email")
    # selects corresponding username data from DB
    cur.execute("SELECT fname, lname, user_id FROM users WHERE email = %s", [current_email])
    data = cur.fetchone()
    # stores what was fetched from the SELECT statement into variables
    fname_session = str(data['fname'])
    lname_session = str(data['lname'])
    userid_session = str(data['user_id'])

    # sidebar data_rev
    ## triple plays
    cur.execute("SELECT COUNT(sale_id) as 'Triple Plays' FROM sales_entry WHERE (vid_unit>0 AND hsd_unit>0 AND voice_unit>0 AND user_id= %s AND Date = CURDATE())", [userid_session])
    data_tp = cur.fetchone()
    triple_plays = data_tp['Triple Plays']
    ## double plays
    cur.execute("SELECT COUNT(sale_id) as 'Double Plays' FROM sales_entry WHERE (vid_unit>0 AND hsd_unit>0 AND voice_unit=0 AND user_id= %s AND Date = CURDATE()) OR (vid_unit>0 AND hsd_unit=0 AND voice_unit>0 AND user_id= %s AND Date = CURDATE()) OR (vid_unit=0 AND hsd_unit>0 AND voice_unit>0 AND user_id= %s AND Date = CURDATE())", [userid_session, userid_session, userid_session])
    data_dp = cur.fetchone()
    double_plays = data_dp['Double Plays']
    ## single plays
    cur.execute("SELECT COUNT(sale_id) as 'Single Plays' FROM sales_entry WHERE (vid_unit>0 AND hsd_unit=0 AND voice_unit=0 AND user_id= %s AND Date = CURDATE()) OR (vid_unit=0 AND hsd_unit>0 AND voice_unit=0 AND user_id= %s AND Date = CURDATE()) OR (vid_unit=0 AND hsd_unit=0 AND voice_unit>0 AND user_id= %s AND Date = CURDATE())", [userid_session, userid_session, userid_session])
    data_sp = cur.fetchone()
    single_plays = data_sp['Single Plays']
    ## total sales
    cur.execute("SELECT COUNT(*) AS 'Total Sales' FROM sales_entry WHERE user_id = %s AND Date = CURDATE()", [userid_session])
    sale_count = cur.fetchone()
    total_sales = int(sale_count['Total Sales'])

    cur.execute("SELECT * FROM sales_entry WHERE user_id = %s AND Date = CURDATE()", [userid_session])
    sales_data = list(cur.fetchall())

    total_vids = 0
    total_hsd = 0
    total_voice = 0
    total_rev = (0)
    total_xh = 0
    total_mobile = 0

    for row in sales_data:
        a = int(row['vid_unit'])
        total_vids += a
    for row in sales_data:
        b = int(row['hsd_unit'])
        total_hsd += b
    for row in sales_data:
        c = int(row['voice_unit'])
        total_voice += c
    for row in sales_data:
        e = int(row['xh_unit'])
        total_xh += e
    for row in sales_data:
        f = int(row['mobile_unit'])
        total_mobile += f
    for row in sales_data:
        d = float(row['revenue'])
        total_rev += d
    total_units = total_vids + total_hsd + total_voice + total_xh + total_mobile
    # percentages
    if total_sales <= 0:
        vid_attach = 0
        tp_percent = 0
        dp_percent = 0
        sp_percent = 0
    elif total_sales >= 1:
        vid_attach = round((float(total_vids) / total_sales) * 100, 2)
        tp_percent = round((float(triple_plays) / total_sales) * 100, 2)
        dp_percent = round((float(double_plays) / total_sales) * 100, 2)
        sp_percent = round((float(single_plays) / total_sales) * 100, 2)

    # date = form.date.data
    vid_unit = form.vid_unit.data
    hsd_unit = form.hsd_unit.data
    voice_unit = form.voice_unit.data
    revenue = form.revenue.data
    xh_unit = form.xh_unit.data
    mobile_unit = form.mobile_unit.data
    chat_id = form.chat_id.data
    cust_id = form.cust_id.data
    comment = form.comment.data
    sesh_id = form.sesh_id.data

    if request.method == 'POST' and form.validate():

        cur.execute("INSERT INTO sales_entry(user_id, Date, FirstName, LastName, vid_unit, hsd_unit, voice_unit, xh_unit, mobile_unit, revenue, chat_id, cust_id, comment, sesh_id) VALUES(%s, CURDATE(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (userid_session, fname_session, lname_session, vid_unit, hsd_unit, voice_unit, xh_unit, mobile_unit, revenue, chat_id, cust_id, comment, sesh_id))
        mysql.connection.commit()

        cur.close()
        flash("Sale Entered!", "success")
        return redirect(url_for('sales_entry'))

    return render_template("sales_entry.html", title="Sales Entry", form=form, name_greet=fname_session, date=todays_date, total_units=total_units, total_vids=total_vids, total_hsd=total_hsd, total_voice=total_voice, total_rev=round(total_rev, 2), vid_attach=vid_attach, sp_percent=sp_percent, dp_percent=dp_percent, tp_percent=tp_percent, table=sales_data)


@app.route("/view_sales", methods=['GET', 'POST'])
@DecoratorWraps.is_logged_in
@DecoratorWraps.check_confirmed
def view_sales():
    """To show sales in a table format"""
    """Top of page should show a dashboard of Total Units
        TOTAL UNITS: XX
        VIDEO: X    INTERNET: X     HSD: X  REVENUE: $XXX"""

    #
    cur = mysql.connection.cursor()

    cur.execute("SELECT DATE_FORMAT(CURDATE(), '%m/%d/%Y') as 'Todays Date' FROM sales_entry")
    data_date = cur.fetchone()
    todays_date = data_date["Todays Date"]

    search = ViewTime_Form(request.form)

    # gets the current logged-in username
    current_email = session.get("email")
    cur.execute("SELECT fname, user_id FROM users WHERE email = %s", [current_email])
    data = cur.fetchone()
    fname_session = str(data['fname'])
    userid_session = str(data['user_id'])

    date_from = search.date_from.data
    date_to = search.date_to.data

    ## triple plays
    cur.execute("SELECT COUNT(sale_id) as 'Triple Plays' FROM sales_entry WHERE (vid_unit>0 AND hsd_unit>0 AND voice_unit>0 AND user_id= %s AND Date >= %s AND Date <= %s)", [userid_session, date_from, date_to])
    data_tp = cur.fetchone()
    triple_plays = data_tp['Triple Plays']
    ## double plays
    cur.execute("SELECT COUNT(sale_id) as 'Double Plays' FROM sales_entry WHERE (vid_unit>0 AND hsd_unit>0 AND voice_unit=0 AND user_id= %s AND Date >= %s AND Date <= %s) OR (vid_unit>0 AND hsd_unit=0 AND voice_unit>0 AND user_id= %s AND Date >= %s AND Date <= %s) OR (vid_unit=0 AND hsd_unit>0 AND voice_unit>0 AND user_id= %s AND Date >= %s AND Date <= %s)", [userid_session, date_from, date_to, userid_session, date_from, date_to, userid_session, date_from, date_to])
    data_dp = cur.fetchone()
    double_plays = data_dp['Double Plays']
    ## single plays
    cur.execute("SELECT COUNT(sale_id) as 'Single Plays' FROM sales_entry WHERE (vid_unit>0 AND hsd_unit=0 AND voice_unit=0 AND user_id= %s AND Date >= %s AND Date <= %s) OR (vid_unit=0 AND hsd_unit>0 AND voice_unit=0 AND user_id= %s AND Date >= %s AND Date <= %s) OR (vid_unit=0 AND hsd_unit=0 AND voice_unit>0 AND user_id= %s AND Date >= %s AND Date <= %s)", [userid_session, date_from, date_to, userid_session, date_from, date_to, userid_session, date_from, date_to])
    data_sp = cur.fetchone()
    single_plays = data_sp['Single Plays']
    ## total sales
    cur.execute("SELECT COUNT(*) AS 'Total Sales' FROM sales_entry WHERE user_id = %s AND Date >= %s AND Date <= %s", [userid_session, date_from, date_to])
    sale_count = cur.fetchone()
    total_sales = int(sale_count['Total Sales'])

    cur.execute("SELECT * FROM sales_entry WHERE user_id = %s AND Date >= %s AND  Date <= %s ORDER BY Date", [userid_session, date_from, date_to])
    sales_data = list(cur.fetchall())

    total_vids = 0
    total_hsd = 0
    total_voice = 0
    total_rev = (0)
    total_xh = 0
    total_mobile = 0

    for row in sales_data:
        a = int(row['vid_unit'])
        total_vids += a
    for row in sales_data:
        b = int(row['hsd_unit'])
        total_hsd += b
    for row in sales_data:
        c = int(row['voice_unit'])
        total_voice += c
    for row in sales_data:
        e = int(row['xh_unit'])
        total_xh += e
    for row in sales_data:
        f = int(row['mobile_unit'])
        total_mobile += f
    for row in sales_data:
        d = float(row['revenue'])
        total_rev += d
    total_units = total_vids + total_hsd + total_voice + total_xh + total_mobile

    # percentages
    if total_sales <= 0:
        vid_attach = 0
        tp_percent = 0
        dp_percent = 0
        sp_percent = 0
    elif total_sales >= 1:
        vid_attach = round((float(total_vids) / total_sales) * 100, 2)
        tp_percent = round((float(triple_plays) / total_sales) * 100, 2)
        dp_percent = round((float(double_plays) / total_sales) * 100, 2)
        sp_percent = round((float(single_plays) / total_sales) * 100, 2)

    if request.method == 'POST':
        if "search" in request.form:
            return render_template('view_sales.html', form=search, name_greet=fname_session, user_id=userid_session, date=todays_date, table=sales_data, total_vids=total_vids, total_hsd=total_hsd, total_voice=total_voice, total_units=total_units, total_rev=round(total_rev,2), vid_attach=vid_attach, sp_percent=sp_percent, dp_percent=dp_percent, tp_percent=tp_percent)
        elif "download" in request.form:
            return download_sales_entry(userid_session, date_from, date_to)

    cur.close()
    return render_template('view_sales.html', form=search, name_greet=fname_session, user_id=userid_session, date=todays_date)


@app.route('/edit_sale/<string:sale_id>', methods=['GET', 'POST'])
@DecoratorWraps.is_logged_in
def edit_sale(sale_id):
    cur = mysql.connection.cursor()
    form = SalesEntryForm(request.form)

    cur.execute("SELECT DATE_FORMAT(CURDATE(), '%m/%d/%Y') as 'Todays Date' FROM sales_entry")
    data_date = cur.fetchone()
    todays_date = data_date["Todays Date"]

    result = cur.execute("SELECT * FROM sales_entry WHERE sale_id = %s", [sale_id])
    entry = cur.fetchone()

    # populate form fields
    form.vid_unit.data = str(entry['vid_unit'])
    form.hsd_unit.data = str(entry['hsd_unit'])
    form.voice_unit.data = str(entry['voice_unit'])
    form.xh_unit.data = str(entry['xh_unit'])
    form.mobile_unit.data = str(entry['mobile_unit'])
    form.revenue.data = str(entry['revenue'])
    form.chat_id.data = entry['chat_id']
    form.cust_id.data = entry['cust_id']
    form.comment.data = entry['comment']

    if request.method == 'POST' and form.validate():
        vid_unit = request.form['vid_unit']
        hsd_unit = request.form['hsd_unit']
        voice_unit = request.form['voice_unit']
        xh_unit = request.form['xh_unit']
        mobile_unit = request.form['mobile_unit']
        revenue = request.form['revenue']
        chat_id = request.form['chat_id']
        cust_id = request.form['cust_id']
        comment = request.form['comment']

        cur.execute("UPDATE sales_entry SET vid_unit=%s, hsd_unit=%s, voice_unit=%s, xh_unit=%s, mobile_unit=%s, revenue=%s, chat_id=%s, cust_id=%s, comment=%s WHERE sale_id=%s", [vid_unit, hsd_unit, voice_unit, xh_unit, mobile_unit, revenue, chat_id, cust_id, comment, sale_id])
        mysql.connection.commit()

        cur.close()
        flash("Sale Updated!", "success")

        return redirect(url_for('sales_entry'))

    return render_template("edit_sale.html", form=form, date=todays_date)


@app.route('/delete_sale/<string:sale_id>', methods=['POST'])
@DecoratorWraps.is_logged_in
def delete_sale(sale_id):
    """delete sales by sale_id"""
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM sales_entry WHERE sale_id = %s", [sale_id])
    mysql.connection.commit()
    cur.close()

    flash('Entry Deleted', 'success')

    return redirect(url_for('sales_entry'))


# log out
@app.route('/logout')
@DecoratorWraps.is_logged_in
def logout():
    session.clear()

    try:
        flash('You are logged out!', 'success')

    except:
        flash('Something went wrong...', "error")
        return render_template("time.html", error=error)

    return redirect(url_for('login'))


@app.route('/view_time', methods=['GET', 'POST'])
@DecoratorWraps.is_logged_in
@DecoratorWraps.check_confirmed
def view_time():
    """This function allows the user to view their time entry from a chosen time period"""
    cur = mysql.connection.cursor()

    cur.execute("SELECT DATE_FORMAT(CURDATE(), '%m/%d/%Y') as 'Todays Date' FROM sales_entry")
    data_date = cur.fetchone()
    todays_date = data_date["Todays Date"]

    search = ViewTime_Form(request.form)

    # gets the current logged-in email
    current_email = session.get("email")
    cur.execute("SELECT fname, user_id FROM users WHERE email = %s", [current_email])
    data = cur.fetchone()
    fname_session = str(data['fname'])
    userid_session = str(data['user_id'])

    date_from = search.date_from.data
    date_to = search.date_to.data

    cur.execute("SELECT * FROM time_entry WHERE user_id = %s AND Date >= %s AND Date <= %s ORDER BY Date", [userid_session, date_from, date_to])
    user_time_list = list(cur.fetchall())

    total_hours = float(0)

    for row in user_time_list:
        a = row['Time_In']
        b = row['Time_Out']
        time_in = datetime.strptime(a, '%H:%M')
        time_out = datetime.strptime(b, '%H:%M')
        time_diff = float((time_out - time_in).seconds)
        total_hours += (time_diff / 3600)


    if request.method == 'POST':
        if "search" in request.form:
            return render_template('view_time.html', form=search, name_greet=fname_session, user_id=userid_session, date=todays_date, table=user_time_list, total=round(total_hours, 2))
        elif "download" in request.form:
            return download_time_entry(userid_session, date_from, date_to)


    cur.close()
    return render_template('view_time.html', form=search, name_greet=fname_session, user_id=userid_session, date=todays_date)


@app.route('/employee_time', methods=['GET', 'POST'])
@DecoratorWraps.authorized
@DecoratorWraps.check_confirmed
def employee_time():
    """This function displays a list of assigned users and can view time entry for a chosen user from the list"""
    cur = mysql.connection.cursor()

    cur.execute("SELECT DATE_FORMAT(CURDATE(), '%m/%d/%Y') as 'Todays Date' FROM sales_entry")
    data_date = cur.fetchone()
    todays_date = data_date["Todays Date"]

    search = ViewTime_Form(request.form)
    user_lookup = search.user_lookup.data
    # gets the current logged-in username
    current_email = session.get("email")
    # selects corresponding username data from DB
    cur.execute("SELECT fname FROM users WHERE email = %s", [current_email])
    data_fname = cur.fetchone()
    fname_session = str(data_fname['fname'])

    cur.execute("SELECT user_id FROM users WHERE email = %s", [current_email])
    data_userid = cur.fetchone()
    userid_session = str(data_userid['user_id'])

    cur.execute("SELECT * FROM users WHERE supe_id = %s", [userid_session])
    employee_list = cur.fetchall()
#####
    date_from = search.date_from.data
    date_to = search.date_to.data

    cur.execute("SELECT * FROM time_entry WHERE user_id = %s AND Date >= %s AND Date <= %s ORDER BY Date", [user_lookup, date_from, date_to])
    user_time_list = list(cur.fetchall())

    total_hours = 0

    for row in user_time_list:
        a = row['Time_In']
        b = row['Time_Out']
        time_in = datetime.strptime(a, '%H:%M')
        time_out = datetime.strptime(b, '%H:%M')
        time_diff = abs((time_out - time_in).seconds)
        total_hours += (time_diff / 3600)

    if request.method == 'POST':
        if "search" in request.form:
            return render_template('employee_time.html', form=search, name_greet=fname_session, user_id=user_lookup, date=todays_date, table=user_time_list, total=round(total_hours,2), user_list=employee_list)
        elif "download" in request.form:
            return download_file(user_lookup, date_from, date_to)

    cur.close()
    return render_template('employee_time.html', form=search, name_greet=fname_session, date=todays_date, user_list=employee_list)


@app.route('/download_time')
def download_time_entry(userid, date_from, date_to):
    """Download time entry as CSV"""
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM time_entry WHERE user_id = %s AND Date >= %s AND Date <= %s ORDER BY Date", [userid, date_from, date_to])
    user_time_list = list(cur.fetchall())

    def generate():
        data = BytesIO()
        #data = StringIO() # for testing purposes

        # write header
        fieldnames = ['Date', 'FirstName', 'LastName', 'Time_In', 'Time_Out', 'category']
        csv_writer = csv.DictWriter(data, fieldnames=fieldnames)
        csv_writer.writeheader()
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        # write each log item
        for row in user_time_list:
            del row['time_id']  # removes columns, ya don't need
            del row['user_id']
            del row['date_submitted']
            csv_writer.writerow(row)

            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    # stream the response as the data is generated
    response = Response(generate(), mimetype='text/csv')
    # add a filename
    response.headers.set("Content-Disposition", "attachment", filename="Time Entry Report.csv")
    return response


@app.route('/download_sales')
def download_sales_entry(userid, date_from, date_to):
    """Download the data for sales"""
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM sales_entry WHERE Date >= %s AND  Date <= %s ORDER BY Date", [date_from, date_to])
    sales_data = list(cur.fetchall())

    def generate():
        data = BytesIO()

        # write header
        fieldnames = ['Date', 'vid_unit', 'hsd_unit', 'voice_unit', 'xh_unit', 'mobile_unit', 'revenue', 'chat_id', 'cust_id', 'comment']
        csv_writer = csv.DictWriter(data, fieldnames=fieldnames)
        csv_writer.writeheader()
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        # write each log item
        for row in sales_data:
            del row['sale_id']  # removes columns, ya don't need
            del row['user_id']
            del row['FirstName']
            del row['LastName']
            del row['date_submitted']
            csv_writer.writerow(row)

            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    # stream the response as the data is generated
    response = Response(generate(), mimetype='text/csv')
    # add a filename
    response.headers.set("Content-Disposition", "attachment", filename="Sales Report.csv")
    return response


@app.route('/sales_dash')
@DecoratorWraps.comcaster
@DecoratorWraps.check_confirmed
def sales_dashboard():
    # time categories
    categories = ["Name","Units", "Revenue"]
    cur = mysql.connection.cursor()
    current_email = session.get('email')
    cur.execute("SELECT fname FROM users WHERE email = %s", [current_email])
    data = cur.fetchone()
    current_fname = str(data['fname'])

    cur.execute("SELECT FirstName, LastName, SUM(vid_unit+hsd_unit+voice_unit+xh_unit+mobile_unit) AS 'Units', ROUND(SUM(revenue),2) AS 'Revenue' FROM sales_entry WHERE Date = CURDATE() GROUP BY user_id ORDER BY Units DESC, Revenue DESC")

    sales_data = list(cur.fetchall())


    return render_template('sales_dashboard.html', name=current_fname, categories=categories, sales_data=sales_data)


@app.route('/dashboard')
@DecoratorWraps.is_logged_in
@DecoratorWraps.check_confirmed
def dashboard():
    # time categories
    categories = ["Time Worked", "Meeting", "Training", "Overtime", "Holiday"]
    cur = mysql.connection.cursor()
    current_email = session.get('email')
    cur.execute("SELECT fname, user_id FROM users WHERE email = %s", [current_email])
    data = cur.fetchone()
    current_fname = str(data['fname'])
    userid_session = str(data['user_id'])

    cur.execute("SELECT * FROM time_entry WHERE user_id = %s AND Date = CURDATE()", [userid_session])
    data_list = list(cur.fetchall())

    total_hours = [time_totals(data_list, category) for category in categories]

    return render_template('dashboard.html', name=current_fname, total_hours=total_hours, categories=categories, data_list=data_list)


def time_totals(data, category):
    # time categories
    categories = ["Time Worked", "Meeting", "Training", "Overtime", "Holiday"]
    total_hours = float(0)
    for row in data:
        if category in row['category']:
            a = row['Time_In']
            b = row['Time_Out']
            time_in = datetime.strptime(a, '%H:%M')
            time_out = datetime.strptime(b, '%H:%M')
            time_diff = float((time_out - time_in).seconds)
            total_hours += (time_diff / 3600)
    return round(total_hours,2)


if __name__ == "__main__":
    app.run(debug=True)
