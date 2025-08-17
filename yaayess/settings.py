import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------------------------------------------
# 🔐 SECURITY
# ----------------------------------------------------
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "5)l#zeh#+4zu)iwd8*4bm2!+bf-%=5n9dpv4um2r(@e!(k(y%j"
)

#DEBUG = False
#ALLOWED_HOSTS = ['168.231.117.6', 'yaayess.com', 'www.yaayess.com']

DEBUG = True
ALLOWED_HOSTS = ['*']

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True  # redirige HTTP vers HTTPS
SECURE_HSTS_SECONDS = 31536000  # active HSTS
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True


"""
ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    "yaayess.com,www.yaayess.com,168.231.117.6"
).split(",")
"""
# ----------------------------------------------------
# 📦 INSTALLED APPS
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

# ----------------------------------------------------
# 🗄 DATABASE (MySQL)
# ----------------------------------------------------


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
# ✉️ EMAIL CONFIG
# ----------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

# ----------------------------------------------------
# 💳 PAYDUNYA CONFIG
# ----------------------------------------------------
"""
PAYDUNYA = {
    "MASTER_KEY": os.environ.get("PAYDUNYA_MASTER_KEY", "EWTNDBmX-0SOD-ZbSr-yoUd-Ir5sntAz6oPu"),
    "PRIVATE_KEY": os.environ.get("PAYDUNYA_PRIVATE_KEY", "test_private_vrIpn4PNbHG5pv5XOrAZALAhOGc"),
    "PUBLIC_KEY": os.environ.get("PAYDUNYA_PUBLIC_KEY", "krIuIZWRPez0Es6h6cHua6rodKy"),
    "TOKEN": os.environ.get("PAYDUNYA_TOKEN", "LRWkyGfcnXSTvRAjUYN7"),
}

PAYDUNYA_MASTER_KEY="EWTNDBmX-0SOD-ZbSr-yoUd-Ir5sntAz6oPu"
PAYDUNYA_PRIVATE_KEY="test_private_vrIpn4PNbHG5pv5XOrAZALAhOGc"
PAYDUNYA_PUBLIC_KEY="krIuIZWRPez0Es6h6cHua6rodKy"
PAYDUNYA_TOKEN="LRWkyGfcnXSTvRAjUYN7"
"""



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


# === Clés API PayDunya ===
PAYDUNYA_KEYS = {
    "master_key": "EWTNDBmX-0SOD-ZbSr-yoUd-Ir5sntAz6oPu",
    "private_key": "test_private_vrIpn4PNbHG5pv5XOrAZALAhOGc",
    "public_key": "krIuIZWRPez0Es6h6cHua6rodKy",
    "token": "LRWkyGfcnXSTvRAjUYN7",
    "mode": "live",  # ou 'sandbox' selon l'environnement
}

AUTHENTICATION_BACKENDS = [
    'accounts.backends.NomBackend',          # connexion via nom
    'django.contrib.auth.backends.ModelBackend',  # fallback standard
]

