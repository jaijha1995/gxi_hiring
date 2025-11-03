import os
from pathlib import Path
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.office365.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('1', 'true', 'yes')
    EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() in ('1', 'true', 'yes')
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'noreply@gxinetworks.com')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
    OTP_LENGTH = int(os.getenv('OTP_LENGTH', 6))  # default 6 digits
    OTP_TTL_SECONDS = int(os.getenv('OTP_TTL_SECONDS', 300))  # 5 minutes
    OTP_RATE_LIMIT_WINDOW = int(os.getenv('OTP_RATE_LIMIT_WINDOW', 300))  # 5 min rate window
    OTP_RATE_LIMIT_MAX = int(os.getenv('OTP_RATE_LIMIT_MAX', 5))  # max 5 per window
    ERROR_RECIPIENT = os.getenv('ERROR_RECIPIENT', 'admin@gxinetworks.com')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')
