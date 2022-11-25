class Config(object):
    SECRET_KEY = "superSecret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.sqlite3"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads/'
    ATTACHMENT_FOLDER = 'static/attachment/'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    STRIPE_CONFIG = ""


class SendMail(object):
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = ""
    MAIL_PASSWORD = ""
    MAIL_DEFAULT_SENDER = ""
    MAIL_MAX_EMAILS = None
    MAIL_ASCII_ATTACHMENTS = False
