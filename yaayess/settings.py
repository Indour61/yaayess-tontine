import os
from pathlib import Path
from dotenv import load_dotenv  # Nouveau module

# Charger les variables d'environnement dès le début
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------------------------------------------
# 🔐 SECURITY - Version corrigée
# ----------------------------------------------------

# SECRET_KEY doit TOUJOURS venir de l'environnement
SECRET_KEY = os.environ["SECRET_KEY"]  # Pas de valeur par défaut!

# Debug doit être conditionné par l'environnement
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# Configuration des hosts dynamique
ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1"
).split(",")

# ----------------------------------------------------
# 🔒 HTTPS Settings (seulement en production)
# ----------------------------------------------------
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    # Désactiver les flags HTTPS en développement
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False

# ----------------------------------------------------
# 📦 INSTALLED APPS (inchangé)
# ----------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Apps locales
    'accounts',
    'cotisationtontine',
    'rest_framework',
    'widget_tweaks',

    # Outils
    'whitenoise.runserver_nostatic',
    'sslserver',
]


# ----------------------------------------------------
# ⚙️ MIDDLEWARE
# ----------------------------------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'yaayess.urls'
WSGI_APPLICATION = 'yaayess.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # ton dossier templates
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

# ----------------------------------------------------
# 🗄 DATABASE - Version sécurisée
# ----------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ["DB_NAME"],
        'USER': os.environ["DB_USER"],
        'PASSWORD': os.environ["DB_PASSWORD"],
        'HOST': os.environ["DB_HOST"],
        'PORT': os.environ["DB_PORT"],
    }
}

# ----------------------------------------------------
# ✉️ EMAIL CONFIG - Version sécurisée
# ----------------------------------------------------
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.environ["EMAIL_HOST_USER"]        # Doit être défini
EMAIL_HOST_PASSWORD = os.environ["EMAIL_HOST_PASSWORD"] # Doit être défini

# ----------------------------------------------------
# 💳 PAYDUNYA CONFIG - Version sécurisée
# ----------------------------------------------------
PAYDUNYA_KEYS = {
    "master_key": os.environ["PAYDUNYA_MASTER_KEY"],
    "private_key": os.environ["PAYDUNYA_PRIVATE_KEY"],
    "public_key": os.environ["PAYDUNYA_PUBLIC_KEY"],
    "token": os.environ["PAYDUNYA_TOKEN"],
    "mode": os.environ.get("PAYDUNYA_MODE", "test"),
}

# ----------------------------------------------------
# 🔑 AUTHENTICATION
# ----------------------------------------------------
AUTH_USER_MODEL = 'accounts.CustomUser'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ----------------------------------------------------
# 🌍 INTERNATIONALIZATION
# ----------------------------------------------------
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Dakar'
USE_I18N = True
USE_TZ = True

# ----------------------------------------------------
# 📁 STATIC & MEDIA FILES
# ----------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'




# ----------------------------------------------------
# 🔒 SECURITY HEADERS (Production)
# ----------------------------------------------------
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True



AUTHENTICATION_BACKENDS = [
    'accounts.backends.NomBackend',          # connexion via nom
    'django.contrib.auth.backends.ModelBackend',  # fallback standard
]

# settings.py
LOGIN_URL = '/accounts/login/'          # redirection pour utilisateurs non connectés
LOGIN_REDIRECT_URL = '/groups/'         # redirection après login réussi

