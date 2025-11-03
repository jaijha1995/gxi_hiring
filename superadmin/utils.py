import os
import logging
from datetime import datetime
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.cache import cache
from django.conf import settings
from django.db import transaction
import random

from .config import Config

# --------------------------
# Custom Logger
# --------------------------
class CustomLogger:
    def __init__(self, app_name, filename=None):
        self.app_name = app_name
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO))

        log_directory = os.path.join(settings.BASE_DIR, 'logs', app_name)
        os.makedirs(log_directory, exist_ok=True)

        if not filename:
            filename = f"{datetime.utcnow().strftime('%Y-%m-%d')}.log"
        log_file_path = os.path.join(log_directory, filename)

        formatter = logging.Formatter(
            '%(asctime)s %(process)d %(thread)s %(levelname)8s '
            '%(filename)s %(funcName)s %(lineno)d %(message)s'
        )

        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)

    def log(self, level, message):
        level = level.lower()
        if level == 'debug':
            self.logger.debug(message, stacklevel=2)
        elif level == 'info':
            self.logger.info(message, stacklevel=2)
        elif level == 'warning':
            self.logger.warning(message, stacklevel=2)
        elif level == 'error':
            self.logger.error(message, stacklevel=2)
        elif level == 'critical':
            self.logger.critical(message, stacklevel=2)
            self.send_critical_email(message)
        else:
            self.logger.info(message, stacklevel=2)

    def send_critical_email(self, message):
        recipient = Config.ERROR_RECIPIENT or getattr(settings, 'ADMINS', None)
        if not recipient:
            self.logger.error("No error recipient configured for critical alerts.")
            return
        subject = f"CRITICAL: {self.app_name} error"
        body = message
        try:
            if isinstance(recipient, (list, tuple)):
                emails = [r[1] if isinstance(r, (list, tuple)) and len(r) > 1 else r for r in recipient]
            else:
                emails = [recipient]
            send_mail(subject, body, Config.DEFAULT_FROM_EMAIL, emails, fail_silently=False)
        except Exception as e:
            self.logger.exception("Failed to send critical email: %s", e)


# --------------------------
# Email Service
# --------------------------
class EmailService:
    @staticmethod
    def send_plain(to_list, subject, message, from_email=None):
        from_email = from_email or Config.DEFAULT_FROM_EMAIL
        send_mail(subject, message, from_email, to_list, fail_silently=False)

    @staticmethod
    def send_html(to_list, subject, template_name, context, from_email=None):
        from_email = from_email or Config.DEFAULT_FROM_EMAIL
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        email = EmailMessage(subject, plain_message, from_email, to_list)
        email.content_subtype = "html"
        email.body = html_message
        email.send(fail_silently=False)


# --------------------------
# OTP helpers with rate-limit via cache
# --------------------------
def generate_otp(length=None):
    length = length or Config.OTP_LENGTH
    start = 10 ** (length - 1)
    end = (10 ** length) - 1
    return str(random.randint(start, end))

def _otp_rate_key(email):
    return f"otp_rate:{email.lower()}"

def send_otp(email, template='otp_email.html', context_extra=None):
    """
    Rate-limited OTP sender. Stores OTP in cache with TTL Config.OTP_TTL_SECONDS.
    Returns (ok: bool, msg: str)
    """
    email = email.lower()
    rate_key = _otp_rate_key(email)
    counter = cache.get(rate_key) or 0
    if counter >= Config.OTP_RATE_LIMIT_MAX:
        return False, "Too many OTP requests. Try again later."

    otp = generate_otp()
    otp_key = f"otp:{email}"
    cache.set(otp_key, otp, Config.OTP_TTL_SECONDS)
    cache.incr(rate_key) if cache.get(rate_key) is not None else cache.set(rate_key, 1, Config.OTP_RATE_LIMIT_WINDOW)

    context = {'otp': otp}
    if context_extra:
        context.update(context_extra or {})

    try:
        EmailService.send_html([email], "Your OTP Code", template, context)
    except Exception as e:
        return False, f"Failed to send OTP email: {e}"

    return True, "OTP sent successfully"

def verify_otp(email, otp):
    email = email.lower()
    otp_key = f"otp:{email}"
    stored = cache.get(otp_key)
    if not stored:
        return False, "OTP expired or not found"
    if str(stored) != str(otp):
        return False, "Invalid OTP"
    cache.delete(otp_key)
    return True, "OTP verified"
