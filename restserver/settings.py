from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-%r@^ik71zj1cy72)g)&zd4q$yb@wf)l%4%pm@l744fdt8!1nt@'
DEBUG = True

ALLOWED_HOSTS = ['*', '3.85.242.139', 'localhost', '127.0.0.1', '13.233.246.56', '13.233.201.179', '192.168.10.194', 'gxi_hiring.jaijhavats.info',]

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
    'candidate_form',
    'google_form_work',
    'form_data',
    'create_job'
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql', 
        'NAME': 'gxi_hiring',                          
        'USER': 'gxi',                
        'PASSWORD': '140806',                
        'HOST': '3.85.242.139',                  
        'PORT': '5432', 
    }
}

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

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



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


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.office365.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL =False
EMAIL_HOST_USER = 'noreply@gxinetworks.com'
EMAIL_HOST_PASSWORD = 'August@082024'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOOGLE_SHEETS_CREDENTIALS_FILE = os.path.join(BASE_DIR, "gxihiring-d7185498ec0f.json")




MS_CLIENT_ID = "6f6e285f-3708-4c01-9071-ad3d619e4811"
MS_CLIENT_SECRET = "rnB8Q~piXZvEJWJlkI8YePVQzGhrIwu_ngAj0cSA"
MS_TENANT_ID = "aadc5d1f-19d3-4ced-a0e5-0aae419ec4d2"
MS_GRAPH_SCOPE = "https://graph.microsoft.com/.default"
MS_TOKEN_URL = f"https://login.microsoftonline.com/{MS_TENANT_ID}/oauth2/v2.0/token"
MS_GRAPH_API_URL = "https://graph.microsoft.com/v1.0"

# For temporary storage of token (in production, use caching or database)
MS_GRAPH_ACCESS_TOKEN = None

# MICROSOFT_CONFIG = {
#     "client_id": "6f6e285f-3708-4c01-9071-ad3d619e4811",
#     "tenant_id": "aadc5d1f-19d3-4ced-a0e5-0aae419ec4d2",
#     "client_secret": "rnB8Q~piXZvEJWJlkI8YePVQzGhrIwu_ngAj0cSA",  # You must generate this below
# }