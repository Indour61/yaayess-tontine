import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # charge automatiquement les variables du fichier .env


BASE_DIR = Path(__file__).resolve().parent.parent


#SECRET_KEY = 'ta_clef_secrète_ici_en_dev'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

if not SECRET_KEY:
    raise ValueError("La variable d'environnement DJANGO_SECRET_KEY n'est pas définie")


#DEBUG = False
#ALLOWED_HOSTS = ['localhost', '127.0.0.1', "yaayess.com", "www.yaayess.com"]

#mode local
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

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

ROOT_URLCONF = 'yaayess.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'yaayessdb',
        'USER': 'yaayessuser',
        'PASSWORD': 'Y@aY3$S!2025',
        'HOST': '168.231.117.6',   # IP du VPS
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}



"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}
"""
# PayDunya Sandbox API Keys


PAYDUNYA_KEYS = {
    "master_key": os.getenv("PAYDUNYA_MASTER_KEY"),
    "private_key": os.getenv("PAYDUNYA_PRIVATE_KEY"),
    "public_key": os.getenv("PAYDUNYA_PUBLIC_KEY"),
    "token": os.getenv("PAYDUNYA_TOKEN"),
}

# Optionnel : vérifier que toutes les clés sont présentes
if not all(PAYDUNYA_KEYS.values()):
    raise ValueError("Toutes les clés PayDunya doivent être définies dans les variables d'environnement.")




AUTH_USER_MODEL = 'accounts.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = 'accounts:login'

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]

"""


import os
from pathlib import Path
from decouple import config  # Décommenté pour éviter l'erreur

# Mode développement
DEBUG = True
ALLOWED_HOSTS = ['*']  # En local on autorise tout

# Chemin de base du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# Sécurité CSRF en local
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'

AUTH_USER_MODEL = 'accounts.CustomUser'

# Applications installées
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

# Authentification
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = 'accounts:login'

# Middleware
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

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

# Base de données locale (Railway dans ton cas)
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

# Clés API depuis .env
SECRET_KEY = config("SECRET_KEY", default="insecure-secret-key")
PAYDUNYA_MASTER_KEY = config("PAYDUNYA_MASTER_KEY", default="")
PAYDUNYA_PRIVATE_KEY = config("PAYDUNYA_PRIVATE_KEY", default="")
PAYDUNYA_TOKEN = config("PAYDUNYA_TOKEN", default="")

# Validation des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalisation
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Fichiers statiques
STATIC_URL = 'static/'

# Clé primaire par défaut
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

"""