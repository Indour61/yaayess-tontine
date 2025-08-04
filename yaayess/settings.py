import os
from pathlib import Path

"""
import firebase_admin
from firebase_admin import credentials

FIREBASE_CRED_PATH = BASE_DIR / 'config/firebase_credentials.json'

# Initialisation unique de Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred)
"""



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-beh4in9sal3s6r%h!s+753@e)8t_fj7i)0#al%8_7!iuen75)_'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

#ALLOWED_HOSTS = []
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']


AUTH_USER_MODEL = 'accounts.CustomUser'


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'accounts',
    'cotisationtontine',
    'rest_framework',
    'widget_tweaks',

]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = '/dashboard/'  # ou l’URL que tu veux après connexion
LOGOUT_REDIRECT_URL = 'accounts:login'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.RoleRequiredMiddleware',

]

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]

ROOT_URLCONF = 'yaayess.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # <--- Vérifie bien cette ligne !
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'yaayess.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bd_yaayess',
        'USER': 'bd_yaayess_user',
        'PASSWORD': 'EJG8HXqiEakEIMekrZcLCY05xoSZBgXk',
        'HOST': 'dpg-d15jtj3uibrs73c2i410-a.oregon-postgres.render.com',
        'PORT': '5432',
        'OPTIONS': {
            # Permet d'utiliser SSL si Render l'exige
            'sslmode': 'require',
        },
    }
}
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'railway',
        'USER': 'postgres',
        'PASSWORD': 'iAXFNusZYoVVnwOYNhuSuiKfGuhOFLXz',
        'HOST': 'hopper.proxy.rlwy.net',
        'PORT': '13805',
    }
}


# PayDunya Sandbox API Keys

PAYDUNYA_KEYS = {
    "master_key": "EWTNDBmX-0SOD-ZbSr-yoUd-Ir5sntAz6oPu",
    "private_key": "test_private_vrIpn4PNbHG5pv5XOrAZALAhOGc",
    "public_key": "krIuIZWRPez0Es6h6cHua6rodKy",
    "token": "LRWkyGfcnXSTvRAjUYN7",

}



# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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

TWILIO_ACCOUNT_SID = "ton_account_sid"
TWILIO_AUTH_TOKEN = "ton_auth_token"
TWILIO_FROM_NUMBER = "+1234567890"  # Ton numéro Twilio



# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
