from flask_mail import Mail, Message
from flask import render_template
from models import app
from config import SendMail

app.config.from_object(SendMail)
mail = Mail(app)


def send_mail(email, image, vehicle_number, location, timestamp):
    print(email)
    msg = Message('Violation Alert')
    msg.recipients.append(str(email))
    msg.html = render_template("mail.html", vehicle_number=vehicle_number, image=image, location=location, timestamp=timestamp)
    mail.send(msg)
    print("Mail Sent")
