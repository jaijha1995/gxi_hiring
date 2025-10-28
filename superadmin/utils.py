import os
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from .config import Config
from django.core.mail import send_mail
from restserver.settings import DEFAULT_FROM_EMAIL, EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD


class CustomLogger:
    def __init__(self, app_name, filename=None):
        self.app_name = app_name
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(getattr(Config, 'LOG_LEVEL', logging.DEBUG))

        log_directory = os.path.join('code', 'logs', app_name)
        os.makedirs(log_directory, exist_ok=True)

        if not filename:
            filename = f"{datetime.now().strftime('%Y-%m-%d')}.log"
        log_file_path = os.path.join(log_directory, filename)

        formatter = logging.Formatter(
            '%(asctime)s %(process)d %(thread)s %(levelname)8s '
            '%(filename)s %(funcName)s %(lineno)d %(message)s'
        )

        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def log(self, level, message):
        valid_levels = ["debug", "info", "warning", "error", "critical"]
        if level.lower() in valid_levels:
            log_method = getattr(self.logger, level.lower(), self.logger.info)
            log_method(message, stacklevel=2)

        if level.lower() == 'critical':
            self.send_critical_email(message)

    def send_critical_email(self, error_message, attachments=None):

        subject = f"Critical Error in {self.app_name}"
        body = f"An error occurred in {self.app_name}:\n\n{error_message}"

        error_recipient = os.getenv("RECIPIENT_MAIL", getattr(Config, 'error_recipient_mail', None))
        if not error_recipient:
            self.log("error", "Error recipient email not configured.")
            return

        send_mail(subject, body, attachments, error_recipient)


def send_email(to_email, subject, message):
    msg = MIMEMultipart()
    msg['From'] = DEFAULT_FROM_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(message, 'plain'))
    
    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.sendmail(DEFAULT_FROM_EMAIL, to_email, msg.as_string())
            server.quit()
    except smtplib.SMTPAuthenticationError as e:
        print("Authentication failed. Please check your credentials:", e)
    except Exception as e:
        print(f"Error sending email: {e}")


import random
import smtplib
from email.mime.text import MIMEText
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import requests

def generate_otp():
    return str(random.randint(1000, 9999))

def send_otp_email(email, otp):
    subject = 'Your OTP'
    message = f'Your OTP is: {otp}'

    from_email = 'jai@skylabstech.com'

    email_message = EmailMessage(subject, message, from_email, [email])
    email_message.send()



def send_welcome_email(email, first_name, last_name):
    subject = 'Welcome to Gxi Hiring'
    html_message = render_to_string('welcome_email_template.html', {
        'email': email,
        'first_name': first_name,
        'last_name': last_name
    })
    plain_message = strip_tags(html_message)
    send_mail(subject, plain_message, '', [email], html_message=html_message)