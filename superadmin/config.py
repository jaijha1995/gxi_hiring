import os
from restserver.settings import DEFAULT_FROM_EMAIL, EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD

class Config:
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    sender_email = DEFAULT_FROM_EMAIL
    smtp_host = EMAIL_HOST
    smtp_port = EMAIL_PORT
    smtp_user = EMAIL_HOST_USER
    smtp_password = EMAIL_HOST_PASSWORD