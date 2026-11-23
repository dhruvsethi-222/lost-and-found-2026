"""
Settings for the Web-Based Lost and Found System.

Anything that is different on your laptop and on PythonAnywhere (the secret key,
debug mode, the database, the email account) is read from environment variables.
On your laptop they come from a file called .env (copy .env.example to .env).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def env(name, default=None):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    return str(env(name, default)).strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name, default=''):
    """Turns 'a, b, c' from the .env file into the list ['a', 'b', 'c']."""
    result = []
    for part in env(name, default).split(','):
        part = part.strip()
        if part:                      # skip empty bits, e.g. after a trailing comma
            result.append(part)
    return result


# ---------------------------------------------------------------- core
SECRET_KEY = env('SECRET_KEY', 'dev-only-key-change-me-before-going-live')
DEBUG = env_bool('DEBUG', True)
ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1')
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS', '')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Our modules (one Django app each, NFR-08)
    'accounts',   # user authentication and role management
    'items',      # reporting lost and found items, Admin intake of found items
    'search',     # searching found items
    'matching',   # back-end matching of lost reports and found items (no pages of its own)
    'claims',     # claiming an item and the Admin's verification decision
    'handover',   # handing an item back to its owner
    'posts',      # posts and replies (the user tweet and response module)
    'core',       # home page, My page, Security desk dashboard, shared templates
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# ---------------------------------------------------------------- database
# Laptop: SQLite (a single file, nothing to install).
# PythonAnywhere: MySQL, switched on with DB_ENGINE=mysql in the .env file.
if env('DB_ENGINE') == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': env('DB_NAME'),
            'USER': env('DB_USER'),
            'PASSWORD': env('DB_PASSWORD'),
            'HOST': env('DB_HOST'),
            'PORT': env('DB_PORT', '3306'),
            'OPTIONS': {'charset': 'utf8mb4', 'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"},
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Every id column is a plain INT, as in the database schema.
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# ---------------------------------------------------------------- accounts and security (NFR-01)
AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
     'OPTIONS': {'user_attributes': ('name', 'email')}},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'core:after_login'
LOGOUT_REDIRECT_URL = 'core:home'

# A session ends after 15 minutes without activity.
SESSION_COOKIE_AGE = 15 * 60
SESSION_SAVE_EVERY_REQUEST = True

# The email verification link works for 3 days.
PASSWORD_RESET_TIMEOUT = 3 * 24 * 60 * 60

# ---------------------------------------------------------------- matching and claims
# A lost report and a found item are saved as a match from this score (out of 100).
MATCH_MINIMUM_SCORE = 50

# The address of the site, used for links inside emails.
SITE_URL = env('SITE_URL', 'http://127.0.0.1:8000')

# Shown to a claimant when a claim is approved.
DESK_COLLECTION_HOURS = env('DESK_COLLECTION_HOURS', 'Monday to Friday, 8:00 am to 5:00 pm')

# ---------------------------------------------------------------- retention (NFR-02)
# How many days a found item is kept at the desk before it can be disposed of.
RETENTION_DAYS = int(env('RETENTION_DAYS', '90'))
# Items this many days from the end of their retention period are shown as "expiring soon".
EXPIRING_SOON_DAYS = 14

# Only campus email addresses can register.
STUDENT_EMAIL_DOMAINS = env_list('STUDENT_EMAIL_DOMAINS', 'students.campus.ac.ke')
STAFF_EMAIL_DOMAINS = env_list('STAFF_EMAIL_DOMAINS', 'campus.ac.ke')

# When the site is live (DEBUG off) everything goes over HTTPS.
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 3600
    SECURE_CONTENT_TYPE_NOSNIFF = True

# ---------------------------------------------------------------- email
# Laptop: emails are printed in the terminal instead of being sent.
# Live: set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend and the account details.
EMAIL_BACKEND = env('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', '')
EMAIL_PORT = int(env('EMAIL_PORT', '587'))
EMAIL_HOST_USER = env('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'Lost and Found <no-reply@campus.ac.ke>')

# ---------------------------------------------------------------- language and time
LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------- files
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'      # collectstatic copies everything here for PythonAnywhere

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'             # photos of found items
MAX_PHOTO_MB = 5

# Bootstrap colours for Django's messages
from django.contrib.messages import constants as message_constants  # noqa: E402

MESSAGE_TAGS = {message_constants.ERROR: 'danger'}
