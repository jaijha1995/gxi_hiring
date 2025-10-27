from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-%r@^ik71zj1cy72)g)&zd4q$yb@wf)l%4%pm@l744fdt8!1nt@'
DEBUG = True

ALLOWED_HOSTS = ['*', '65.2.44.234', 'localhost', '127.0.0.1', '13.233.246.56', '13.233.201.179', '192.168.10.194', 'gxi_hiring.jaijhavats.info',]

AUTH_USER_MODEL =  'superadmin.UserProfile'


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'superadmin',
    'google_sheet',
    'profile_details',
    'channels',
    'google_form_work'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'restserver.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


CSRF_TRUSTED_ORIGINS = [
    'https://gxi_hiring.jaijhavats.info/'
]

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}





ROOT_URLCONF = 'restserver.urls'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=3600), 
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB or more
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760

IMPORT_EXPORT_USE_TRANSACTIONS = True



LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}



WSGI_APPLICATION = 'restserver.wsgi.application'
ASGI_APPLICATION = 'restserver.asgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',   # Use PostgreSQL backend
        'NAME': 'gxi_hiring',                             # Database name
        'USER': 'gxi',                          # PostgreSQL username
        'PASSWORD': '140806',                        # PostgreSQL password
        'HOST': '13.234.77.222',                         # Database host (use IP if remote)
        'PORT': '5432',                              # Default PostgreSQL port
    }
}


# settings.py

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',   # Use PostgreSQL backend
#         'NAME': 'Gxi_Hiring',                             # Database name
#         'USER': 'postgres',                          # PostgreSQL username
#         'PASSWORD': '140806',                        # PostgreSQL password
#         'HOST': 'localhost',                         # Database host (use IP if remote)
#         'PORT': '5432',                              # Default PostgreSQL port
#     }
# }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/


CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/0"
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

LANGUAGE_CODE = 'en-us'
USE_I18N = True
TIME_ZONE = 'Asia/Kolkata'
USE_TZ = True



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",  # For development only
#         "LOCATION": "unique-snowflake",
#         "TIMEOUT": None,
#     }
# }


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'cache'),
        'TIMEOUT': 20,  # 24 hours (in seconds)
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}


# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "redis://127.0.0.1:6379/1",
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         }
#     }
# }



EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'                 # Gmail SMTP server
EMAIL_PORT = 587                              # Port for TLS
EMAIL_USE_TLS = True                          # Use TLS
EMAIL_HOST_USER = 'atul@mioneer.in'      # Your Gmail address
EMAIL_HOST_PASSWORD = 'udga euzi cpal gfnu'     # Gmail app password (not your regular password)
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER





# settings.py

# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.zoho.com'
# EMAIL_PORT = 465
# EMAIL_USE_SSL = True
# EMAIL_USE_TLS = False
# EMAIL_HOST_USER = 'jaijhavats@zohomail.in'
# EMAIL_HOST_PASSWORD = 'DrgWJwmYQBXJ'  # Use App Password
# DEFAULT_FROM_EMAIL = EMAIL_HOST_USER



# EMAIL_HOST_PASSWORD = 'KCfAFH7xjHQ8'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOOGLE_SHEETS_CREDENTIALS_FILE = os.path.join(BASE_DIR, "gxihiring-d7185498ec0f.json")

