from flask import Flask
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
db = SQLAlchemy()


class Disputes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(120))
    challan_number = db.Column(db.String(80))
    vehicle_number = db.Column(db.String(80))
    reason = db.Column(db.String(80))
    description = db.Column(db.Text)
    is_resolved = db.Column(db.Boolean)
    is_cancelled = db.Column(db.Boolean)
    comment = db.Column(db.Text)
    police_attachment = db.Column(db.String(80))
    attachment = db.Column(db.String(80))
    
    def __init__(self, name, email, challan_number, vehicle_number, reason, 
                 description, is_resolved, is_cancelled, comment, police_attachment, attachment):
        self.name = name
        self.email = email
        self.challan_number = challan_number
        self.vehicle_number = vehicle_number
        self.reason = reason
        self.description = description
        self.is_resolved = is_resolved
        self.is_cancelled = is_cancelled
        self.comment = comment
        self.police_attachment = police_attachment
        self.attachment = attachment


class AllUsers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    vehicle_number = db.Column(db.String(80))
    email = db.Column(db.String(120))
    phone_number = db.Column(db.String(80))
    address = db.Column(db.String(120))
    chasis_number = db.Column(db.String(80))

    def __init__(self, first_name, last_name, vehicle_number, email, phone_number, address, chasis_number):
        self.first_name = first_name
        self.last_name = last_name
        self.vehicle_number = vehicle_number
        self.email = email
        self.phone_number = phone_number
        self.address = address
        self.chasis_number = chasis_number


class Videos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_file_name = db.Column(db.String(256))
    user_name = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, default=datetime.now())

    def __init__(self, video_file_name, user_name, timestamp):
        self.video_file_name = video_file_name
        self.user_name = user_name
        self.timestamp = timestamp


class Violators(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_file_name = db.Column(db.String(256))
    station_name = db.Column(db.String(256))
    user_name = db.Column(db.String(256))
    image_file_name = db.Column(db.String(256))
    location = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, default=datetime.now())
    category = db.Column(db.String(256))
    number_plate = db.Column(db.String(256))
    is_approved = db.Column(db.Boolean)
    img = db.Column(db.Text, nullable=False)
    number_plate_img = db.Column(db.Text, nullable=False)
    payment_status = db.Column(db.Boolean)

    def __int__(self,
                video_file_name, station_name, user_name, image_file_name, location, timestamp, category, is_approved,
                number_plate, img, number_plate_img, payment_status):
        self.video_file_name = video_file_name
        self.station_name = station_name
        self.user_name = user_name
        self.image_file_name = image_file_name
        self.location = location
        self.timestamp = timestamp
        self.category = category
        self.is_approved = is_approved
        self.number_plate = number_plate
        self.img = img
        self.number_plate_img = number_plate_img
        self.payment_status = payment_status


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(256), unique=True)
    police_station = db.Column(db.String(256))
    location = db.Column(db.String(256))
    password = db.Column(db.String(256))

    def __init__(self, user_name, password, police_station, location):
        self.user_name = user_name
        self.police_station = police_station
        self.location = location
        if password is not None:
            self.password = generate_password_hash(password)
        else:
            self.password = password

    def check_password(self, password):
        return check_password_hash(self.password, password)


login_manager = LoginManager()
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))
