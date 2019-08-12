from project_lib import *
import secret_key

app = Flask(__name__)

app.secret_key = secret_key.secret_key

# Configure this environment variable via app.yaml
#CLOUD_STORAGE_BUCKET = os.environ['CLOUD_STORAGE_BUCKET']


# Config  MySQL
app.config['MYSQL_UNIX_SOCKET'] = str(db.MYSQL_UNIX_SOCKET)
app.config['MYSQL_HOST'] = str(db.MYSQL_HOST)
app.config['MYSQL_USER'] = str(db.MYSQL_USER)
app.config['MYSQL_PASSWORD'] = str(db.MYSQL_PASSWORD)
app.config['MYSQL_DB'] = str(db.MYSQL_DB)
app.config['MYSQL_CURSORCLASS'] = str(db.MYSQL_CURSORCLASS)

# init MYSQL
mysql = MySQL(app)

now = datetime.now()
todays_date = now.strftime("%m/%d/%Y")
sql_format = now.strftime("%Y-%m-%d")


# @ signifies a decorator - way to wrap a function and modifying its behavior

@app.route("/")
def index():
    return render_template('home.html')


@app.route("/about")
def about():
    return render_template('about.html', title='About')


# checks if user logged in
def authorized(f):
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
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


# user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        fname = form.fname.data
        lname = form.lname.data
        email = form.email.data

        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Executes the query statement
        cur.execute("INSERT INTO users(fname, lname, email, password) VALUES(%s, %s, %s, %s)", (fname, lname, email, password))

        # commit to DB
        mysql.connection.commit()

        # close connection
        cur.close()

        flash('You are now officially registered and can login!', 'success')

        return redirect(url_for('login'))

    return render_template('register.html', form=form, title='Register!')


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
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

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Account not found'
            return render_template('login.html', error=error)


    return render_template('login.html', title='Login')


@app.route('/time_entry', methods=['GET', 'POST'])
@is_logged_in
def time_entry():
    cur = mysql.connection.cursor()
    form = TimeEntry_Form(request.form)

    current_email = session.get("email")
    # selects corresponding username data from DB
    cur.execute("SELECT fname FROM users WHERE email = %s", [current_email])
    data_fname = cur.fetchone()
    cur.execute("SELECT lname FROM users WHERE email = %s", [current_email])
    data_lname = cur.fetchone()
    cur.execute("SELECT user_id FROM users WHERE email = %s", [current_email])
    data_userid = cur.fetchone()
    # stores what was fetched from the SELECT statement into variables
    fname_session = str(data_fname['fname'])
    lname_session = str(data_lname['lname'])
    userid_session = str(data_userid['user_id'])

    if request.method == 'POST' and form.validate():
        date = form.date_form.data
        time_in = form.time_in_form.data
        time_out = form.time_out_form.data
        # execute time info into database
        cur.execute("INSERT INTO time_entry(user_id, Date, FirstName, LastName, Time_In, Time_Out) VALUES(%s, %s, %s, %s, %s, %s)", (userid_session, date, fname_session, lname_session, time_in, time_out))

        # commit to DB
        mysql.connection.commit()
        # close the connection
        cur.close()

        flash("Time entry submitted!", 'success')
        print("Entry Received!")
    return render_template('time.html', title='Time Entry', form=form, name_greet=fname_session, date=todays_date)


@app.route("/sales_entry", methods=['GET', 'POST'])
def sales_entry():
    """page to add sales"""
    """Needs similar formatting to time_entry function"""

    cur = mysql.connection.cursor()
    form = SalesEntryForm(request.form)

    current_email = session.get("email")
    # selects corresponding username data from DB
    cur.execute("SELECT fname FROM users WHERE email = %s", [current_email])
    data_fname = cur.fetchone()
    cur.execute("SELECT lname FROM users WHERE email = %s", [current_email])
    data_lname = cur.fetchone()
    cur.execute("SELECT user_id FROM users WHERE email = %s", [current_email])
    data_userid = cur.fetchone()
    # stores what was fetched from the SELECT statement into variables
    fname_session = str(data_fname['fname'])
    lname_session = str(data_lname['lname'])
    userid_session = str(data_userid['user_id'])

    if request.method == 'POST' and form.validate():
        # date = form.date.data
        vid_unit = form.vid_unit.data
        hsd_unit = form.hsd_unit.data
        voice_unit = form.voice_unit.data
        revenue = form.revenue.data
        chat_id = form.chat_id.data
        cust_id = form.cust_id.data
        comment = form.comment.data

        cur.execute("INSERT INTO sales_entry(user_id, Date, FirstName, LastName, vid_unit, hsd_unit, voice_unit, revenue, chat_id, cust_id, comment) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (userid_session, sql_format, fname_session, userid_session, vid_unit, hsd_unit, voice_unit, revenue, chat_id, cust_id, comment))
        mysql.connection.commit()
        cur.close()

        flash("Sale Entered!", "success")

    return render_template("sales_entry.html", title="Sales Entry", form=form, name_greet=fname_session, date=todays_date)

@app.route("/view_sales", methods=['GET', 'POST'])
def view_sales():
    """To show sales in a table format"""
    """Top of page should show a dashboard of Total Units
        TOTAL UNITS: XX
        VIDEO: X    INTERNET: X     HSD: X  REVENUE: $XXX"""

    #
    cur = mysql.connection.cursor()
    search = ViewTime_Form(request.form)

    # gets the current logged-in username
    current_email = session.get("email")
    cur.execute("SELECT fname FROM users WHERE email = %s", [current_email])
    data_fname = cur.fetchone()
    fname_session = str(data_fname['fname'])

    cur.execute("SELECT user_id FROM users WHERE email = %s", [current_email])
    data_userid = cur.fetchone()
    userid_session = str(data_userid['user_id'])

    date_from = search.date_from.data
    date_to = search.date_to.data

    cur.execute("SELECT * FROM sales_entry WHERE Date >= %s AND  Date <= %s", [date_from, date_to])
    sales_data = list(cur.fetchall())

    total_vids = 0
    total_hsd = 0
    total_voice = 0
    total_rev = (0)
    for row in sales_data:
        a = row['vid_unit']
        total_vids += a
    for row in sales_data:
        b = row['hsd_unit']
        total_hsd += b
    for row in sales_data:
        c = row['voice_unit']
        total_voice += c
    for row in sales_data:
        d = row['revenue']
        total_rev += d
    total_units = total_vids + total_hsd + total_voice


    table = SalesTable(sales_data, no_items="No sales yet. Start selling something!!", )
    table.border = True
    table.html_attrs = {"align":"center", "style":"font-family:Tahoma; width:100%; text-align:center; background-color: #228228228; box-shadow:5px 5px 10px black"}
    table.classes = ["lead"]


    if request.method == 'POST':
        if "search" in request.form:
            return render_template('view_sales.html', form=search, name_greet=fname_session, user_id=userid_session, date=todays_date, table=table, total_vids=total_vids, total_hsd=total_hsd, total_voice=total_voice, total_units=total_units, total_rev=float(total_rev))
        elif "download" in request.form:
            return download_sales_entry(userid_session, date_from, date_to)

    cur.close()
    return render_template('view_sales.html', form=search, name_greet=fname_session, user_id=userid_session, date=todays_date)

# log out
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()

    try:
        flash('You are logged out!', 'success')

    except:
        flash('Something went wrong...', "error")
        return render_template("time.html", error=error)

    return redirect(url_for('login'))


@app.route('/view_time', methods=['GET', 'POST'])
@is_logged_in
def view_time():
    """This function allows the user to view their time entry from a chosen time period"""
    cur = mysql.connection.cursor()
    search = ViewTime_Form(request.form)

    # gets the current logged-in username
    current_email = session.get("email")
    cur.execute("SELECT fname FROM users WHERE email = %s", [current_email])
    data_fname = cur.fetchone()
    fname_session = str(data_fname['fname'])

    cur.execute("SELECT user_id FROM users WHERE email = %s", [current_email])
    data_userid = cur.fetchone()
    userid_session = str(data_userid['user_id'])

    date_from = search.date_from.data
    date_to = search.date_to.data

    cur.execute("SELECT * FROM time_entry WHERE user_id = %s AND Date >= %s AND Date <= %s", [userid_session, date_from, date_to])
    user_time_list = list(cur.fetchall())

    total_hours = 0

    for row in user_time_list:
        a = row['Time_In']
        b = row['Time_Out']
        time_in = datetime.strptime(a, '%H:%M')
        time_out = datetime.strptime(b, '%H:%M')
        time_diff = abs((time_out - time_in).seconds)
        total_hours += (time_diff / 3600)

    table = ResultTable(user_time_list, no_items="There's NOTHING")
    table.border = True
    #table.get_tr_attrs = {"align":"text-center"}
    table.html_attrs = {"align":"center", "style":"font-family:Tahoma; width:80%; text-align:center; background-color: #228228228; box-shadow:5px 5px 10px black"}
    table.classes = ["lead"]


    if request.method == 'POST':
        if "search" in request.form:
            return render_template('view_time.html', form=search, name_greet=fname_session, user_id=userid_session, date=todays_date, table=table, total=round(total_hours,2))
        elif "download" in request.form:
            return download_time_entry(userid_session, date_from, date_to)

    cur.close()
    return render_template('view_time.html', form=search, name_greet=fname_session, user_id=userid_session, date=todays_date)


@app.route('/employee_time', methods=['GET', 'POST'])
@authorized
def employee_time():
    """This function displays a list of assigned users and can view time entry for a chosen user from the list"""
    cur = mysql.connection.cursor()
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

    cur.execute("SELECT * FROM time_entry WHERE user_id = %s AND Date >= %s AND Date <= %s", [user_lookup, date_from, date_to])
    user_time_list = list(cur.fetchall())

    total_hours = 0

    for row in user_time_list:
        a = row['Time_In']
        b = row['Time_Out']
        time_in = datetime.strptime(a, '%H:%M')
        time_out = datetime.strptime(b, '%H:%M')
        time_diff = abs((time_out - time_in).seconds)
        total_hours += (time_diff / 3600)

    table = ResultTable(user_time_list, no_items="There's NOTHING", )
    table.border = True
    table.html_attrs = {"align":"center", "style":"font-family:Tahoma; background-color: #228228228; box-shadow:5px 5px 10px black"}
    table.classes = ["lead"]


    if request.method == 'POST':
        if "search" in request.form:
            return render_template('employee_time.html', form=search, name_greet=fname_session, user_id=user_lookup, date=todays_date, table=table, total=round(total_hours,2), user_list=employee_list)
        elif "download" in request.form:
            return download_file(user_lookup, date_from, date_to)

    cur.close()
    return render_template('employee_time.html', form=search, name_greet=fname_session, date=todays_date, user_list=employee_list)


@app.route('/download_time')
def download_time_entry(userid, date_from, date_to):
    """Download time entry as CSV"""
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM time_entry WHERE user_id = %s AND Date >= %s AND Date <= %s", [userid, date_from, date_to])
    user_time_list = list(cur.fetchall())

    def generate():
        data = BytesIO()

        # write header
        fieldnames = ['Date', 'FirstName', 'LastName', 'Time_In', 'Time_Out']
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

    cur.execute("SELECT * FROM sales_entry WHERE Date >= %s AND  Date <= %s", [date_from, date_to])
    sales_data = list(cur.fetchall())

    def generate():
        data = BytesIO()

        # write header
        fieldnames = ['Date', 'vid_unit', 'hsd_unit', 'voice_unit', 'revenue', 'chat_id', 'cust_id', 'comment']
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


@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()
    current_email = session.get('email')
    cur.execute("SELECT fname FROM users WHERE email = %s", [current_email])
    data = cur.fetchone()
    current_fname = str(data['fname'])
    return render_template('dashboard.html', name=current_fname)




if __name__ == "__main__":
    app.run(debug=True)
