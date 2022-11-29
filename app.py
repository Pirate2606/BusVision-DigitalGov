from flask import render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_login import login_user, logout_user, login_required
from wtforms import ValidationError
from werkzeug.utils import secure_filename
from models import app, db, Users, login_manager, Violators, Videos, AllUsers, Disputes
from config import Config
from main import *
import uuid
import datetime
from multiprocessing import Process
import stripe

# configuring the app
app.config.from_object(Config)
db.init_app(app)
login_manager.init_app(app)
stripe.api_key = app.config['STRIPE_CONFIG']


@app.before_first_request
def before_first_request():
    db.create_all()
    first_names = ["Aditya", "Harshita", "Rajiv", "Shrihari",
                   "Vivek", "Kunal", "Seema", "Harsh", "Alpana", "Ajay"]
    last_names = ["Naitan", "Ashwani", "Sharma", "K", "Singh",
                  "Salaria", "Sharma", "Kumar", "Singh", "Sharma"]
    vehicle_numbers = ["HP37A2193", "PB37A2193", "MP37A2193", "UP37A2193",
                       "WB42AC2530", "HP37A2993", "WB37A1393", "RJ37A3193", "X477ELF", "HP37A8973"]
    emails = ["naitan@gmail.com", "ashwani@gmail.com", "sharma@gmail.com", "shrihari@gmail.com",
              "adityanaitan@gmail.com",
              "salaria@gmail.com", "hashwani@deloitte.com", "kumar@gmail.com", "singh@gmail.com", "ajay@gmail.com"]
    phone_numbers = ["1234567898", "1234567534", "1234569876", "9876543235",
                     "9876245781", "9876549871", "9883457852", "9876578512", "9876541204", "9876540912"]
    addresses = [
        "New Shimla, Shimla",
        "214, 1st Floor, Monica Tower, Jalandhar",
        "Hotel Jacksons Rd, Civil Lines, Jabalpur",
        "E 65-66 Sector 8, Noida",
        "P-122, C I T Road, Kankurgachi, Kolkata",
        "H-23, Palampur, H.P.",
        "20/2/1, Gariahat Road (s), Dhakuria, Kolkata",
        "18, Gali 7, Bhudatt Colony, Ballabhgarh",
        "6th Floor, Nr Lions Hall, Mithakhali, Ahmedabad",
        "B-16, Sector-2, Dharamshala, Kangra"
    ]
    chasis_number = ["12345676543456768", "12345676543456761", "12345676543456762", "12345676543456763",
                     "12345676543456764", "12345676543456765", "12345676543456766", "12345676543456767",
                     "12345676543456769", "12345676543456760"
                     ]
    get_users = AllUsers.query.all()
    if len(get_users) != 10:
        for i in range(len(first_names)):
            user = AllUsers(
                first_names[i],
                last_names[i],
                vehicle_numbers[i],
                emails[i],
                phone_numbers[i],
                addresses[i],
                chasis_number[i]
            )
            db.session.add(user)
    db.session.commit()


@app.route('/user')
def landing_page():
    return render_template('landing_page.html')


@app.route('/user/check-violation', methods=["GET", "POST"])
def check_violation():
    if request.method == "POST":
        images = []
        count = 0
        vehicle_number = request.form['vehicle_number']
        chasis_number = request.form['chasis_number']
        violator = Violators.query.filter_by(
            number_plate=vehicle_number.upper()).all()
        if len(violator) != 0:
            user = AllUsers.query.filter_by(
                vehicle_number=vehicle_number).first()
            dispute_raised = []
            is_resolved = []
            is_cancelled = []
            if user.chasis_number[13:] == chasis_number:
                for v in violator:
                    if v.payment_status:
                        count += 1
                    challan_number = str(v.id) + '_' + str(v.video_file_name)
                    dispute = Disputes.query.filter_by(challan_number=challan_number).first()
                    if dispute is not None:
                        dispute_raised.append(True)
                        is_resolved.append(dispute.is_resolved)
                        is_cancelled.append(dispute.is_cancelled)
                    else:
                        dispute_raised.append(False)
                    images.append(v.img)
                if count == len(violator):
                    flash(
                        f"No new violation found, <a style='text-decoration: none; margin-left: 10px;' href='/user/history?n={violator[0].number_plate}'>View history</a>")
                    return redirect(url_for('check_violation'))
                return render_template(
                    'violation_status.html',
                    violator=violator,
                    images=images,
                    number_plate=violator[0].number_plate,
                    no_violation=False,
                    rows=len(violator),
                    dispute_raised=dispute_raised,
                    is_resolved=is_resolved,
                    is_cancelled=is_cancelled
                )
            else:
                flash(f"Chassis number does not match.")
                return redirect(url_for('check_violation'))
        else:
            flash(f"No violations found for given vehicle number.")
            return redirect(url_for('check_violation'))
    return render_template('violation_status.html', violator=None, no_violation=False, rows=0)


@app.route('/user/disputes/<challan_num>', methods=["GET", "POST"])
def disputes(challan_num):
    # challan_num = id + _ + videoName
    if request.method == "POST":
        file_name = ""
        name = request.form['name']
        email = request.form['email']
        vehicle_number = request.form['vehicle_number']
        reason = request.form['reason']
        description = request.form['description']
        file = request.files['attachment']
        if file:
            file_name = challan_num + "." + str(file.filename.split(".")[-1])
            filename = secure_filename(file_name)
            file.save(os.path.join(app.config['ATTACHMENT_FOLDER'], filename))
        disputes = Disputes(name, email, challan_num,
                            vehicle_number, reason, description, False, False, "", "", file_name)
        db.session.add(disputes)
        db.session.commit()
        return render_template('success_dispute.html')
    return render_template('disputes.html')


@app.route('/user/history')
def show_history():
    number_plate = request.args.get('n')
    images = []
    violators = Violators.query.filter_by(number_plate=number_plate).all()
    user = AllUsers.query.filter_by(vehicle_number=number_plate).first()
    if violators is not None:
        for v in violators:
            images.append(v.img)
    disputes = Disputes.query.filter_by(vehicle_number=number_plate).all()
    dispute_violator = []
    if disputes is not None:
        for d in disputes:
            id_ = d.challan_number.split("_")[0]
            dispute_violator.append(Violators.query.filter_by(id=id_).first())
    return render_template(
        'show_history.html',
        disputes=disputes,
        violators=violators,
        rows=len(violators),
        disputes_rows=len(disputes),
        images=images,
        dispute_violator=dispute_violator,
        name=user.first_name + " " + user.last_name
    )


@app.route('/', methods=["GET", "POST"])
def home():
    # If user is not logged in, redirect them to register page
    if not session.get("user_id"):
        return redirect(url_for('register'))
    images = []
    user = Users.query.filter_by(id=session["user_id"]).first()
    if request.method == "POST":
        search = request.form['search']
        lane_violators = Violators.query.filter_by(number_plate=search).all()
    else:
        lane_violators = Violators.query.filter_by(
            location=user.location).all()
    if lane_violators is not None:
        for v in lane_violators:
            images.append(v.img)
    return render_template('dashboard.html', violators=lane_violators, images=images)


@app.route('/download/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    uploads = os.path.join(os.getcwd(), app.config['ATTACHMENT_FOLDER'])
    return send_from_directory(uploads, filename)


@app.route('/disputes', methods=["GET", "POST"])
@login_required
def admin_disputes():
    if request.method == "POST":
        id_ = request.args.get('id')
        is_resolved = request.form['is_resolved']
        comment = request.form['comment']
        file = request.files['attachment']
        dispute = Disputes.query.filter_by(id=id_).first()
        if dispute is not None:
            if is_resolved == "True":
                violator = Violators.query.filter_by(number_plate=dispute.vehicle_number).first()
                if violator is not None:
                    violator.payment_status = True
                    db.session.add(violator)
            if file:
                file_name = dispute.challan_number + "-police." + str(file.filename.split(".")[-1])
                filename = secure_filename(file_name)
                file.save(os.path.join(app.config['ATTACHMENT_FOLDER'], filename))
                dispute.police_attachment = file_name
            dispute.is_resolved = 'True' == is_resolved
            dispute.is_cancelled = 'False' == is_resolved
            dispute.comment = comment
            db.session.add(dispute)
            db.session.commit()
        disputes = Disputes.query.all()
        return render_template('disputes_admin.html', disputes=disputes)
    disputes = Disputes.query.all()
    return render_template('disputes_admin.html', disputes=disputes)


@app.route('/user/pay-challan', methods=['POST'])
def pay_challan():
    try:
        id_ = request.args.get('n')
        num = f"?n={id_}"
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': 'price_1LEBvkSHVFhB1h9xSZgZkkrE',
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=url_for('success', _external=True) + str(num),
            cancel_url=url_for('cancel', _external=True),
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)


@app.route('/user/success')
def success():
    id_ = request.args.get('n')
    violator = Violators.query.filter_by(id=id_).first()
    if violator is not None:
        violator.payment_status = True
        db.session.add(violator)
        db.session.commit()
    return render_template('success.html')


@app.route('/user/cancel')
def cancel():
    return render_template('cancel.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    username_flag = False
    password_flag = False
    if request.method == 'POST':
        username = request.form['username']
        # Checking for duplicate username
        try:
            check_username(username)
        except ValidationError:
            username_flag = True

        if username_flag:
            return render_template('register.html', username_flag=username_flag, password_flag=password_flag)

        # Comparing password and confirm password fields
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            password_flag = True
        if password_flag:
            return render_template('register.html', username_flag=username_flag, password_flag=password_flag)

        # Getting data from form
        police_station = request.form['police_station']
        location = request.form['location']

        # Adding data to database
        user = Users(username, password, police_station, location.lower())
        db.session.add(user)
        db.session.commit()

        # Logging in user
        session['user_id'] = user.id
        login_user(user)
        return redirect(url_for('home'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get("user_id"):
        return redirect(url_for('home'))
    flag = False
    if request.method == "POST":
        # Fetching user from database
        user = Users.query.filter_by(
            user_name=request.form['username']).first()
        if user is not None:
            if user.check_password(request.form['password']):
                user = Users.query.filter_by(user_name=user.user_name).first()

                # If password and username is correct, then log in the user
                session['user_id'] = user.id
                login_user(user)
                return redirect(url_for("home"))
            else:
                flag = True
        else:
            flag = True
    return render_template('login.html', flag=flag)


@app.route("/logout")
@login_required
def logout():
    session.pop('user_id', None)
    logout_user()
    return redirect(url_for("home"))


@app.route('/add-video', methods=['GET', 'POST'])
@login_required
def add_video():
    if request.method == "POST":
        if 'video' not in request.files:
            flash('No file part')
            return redirect(url_for("add_video"))
        file = request.files['video']
        if file.filename == '':
            flash('No video selected for uploading')
            return redirect(url_for("add_video"))
        else:
            # Saving the uploaded video in the UPLOAD_FOLDER
            unique_filename = str(uuid.uuid4().hex[:8]) + '.mp4'
            filename = secure_filename(unique_filename)
            video_name = filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Getting current user details
            user = Users.query.filter_by(id=session['user_id']).first()
            video = Videos(video_file_name=video_name.split(".")[0], user_name=user.user_name, timestamp=datetime.datetime.now())
            db.session.add(video)
            db.session.commit()

            location = request.form['location']
            background_thread = Process(
                target=main,
                args=(
                    app.config['UPLOAD_FOLDER'] + filename,
                    video_name,
                    user.police_station,
                    user.user_name,
                    location.lower(),
                    file.filename
                )
            )
            background_thread.start()
            return redirect(url_for("show_violators", video_name=video_name.split(".")[0]))
    return render_template('add_video.html')


@app.route('/video/<video_name>')
@login_required
def show_violators(video_name):
    video = video_name.split(".")[0]
    number_plate_images = []
    images = []
    viol = Violators.query.filter_by(video_file_name=video).all()
    if len(viol) == 0:
        viol = None
    if viol is not None:
        for v in viol:
            images.append(v.img)
            number_plate_images.append(v.number_plate_img)
    return render_template("show_violators.html", violator=viol, images=images, number_plate_images=number_plate_images)


@app.route('/all/videos')
@login_required
def all_videos():
    status = []
    user = Users.query.filter_by(id=session['user_id']).first()
    all_videos_ = Videos.query.filter_by(user_name=user.user_name).all()
    for video in all_videos_:
        if Violators.query.filter_by(video_file_name=video.video_file_name).first() is None:
            status.append("Processing")
        else:
            status.append("Done")
    all_videos_.reverse()
    status.reverse()
    return render_template("all-videos.html", all_videos=all_videos_, status=status)


# 404 Error handler
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


# 403 Error handler
@app.errorhandler(403)
def page_not_found(error):
    return render_template('403.html'), 403


def check_username(data):
    # Checking if username already exists in database
    if Users.query.filter_by(user_name=data).first():
        raise ValidationError('This username is already registered.')
    else:
        return False


if __name__ == '__main__':
    app.run()
