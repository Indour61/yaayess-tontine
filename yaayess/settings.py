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

DEBUG = False
ALLOWED_HOSTS = ['168.231.117.6', 'yaayess.com', 'www.yaayess.com']

#DEBUG = True
#ALLOWED_HOSTS = ['*']

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
        'ENGINE': os.environ.get("DB_ENGINE", "django.db.backends.mysql"),
        'NAME': os.environ.get("DB_NAME", "yaayessdb"),
        'USER': os.environ.get("DB_USER", "yaayessuser"),
        'PASSWORD': os.environ.get("DB_PASSWORD", "Y@aY3$S!2025"),
        'HOST': os.environ.get("DB_HOST", "168.231.117.6"),
        'PORT': os.environ.get("DB_PORT", "3306"),
        'OPTIONS': {
            'init_command': os.environ.get(
                "DB_INIT_COMMAND", "SET sql_mode='STRICT_TRANS_TABLES'"
            ),
            'charset': os.environ.get("DB_CHARSET", "utf8mb4"),
        }
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





"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Clé secrète (toujours définir SECRET_KEY dans les variables d'env)
SECRET_KEY = os.environ.get("SECRET_KEY", "insecure-default-key")

# Mode DEBUG
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# Hôtes autorisés (liste séparée par des virgules)
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Base de données (exemple MySQL)
DATABASES = {
    'default': {
        'ENGINE': os.environ.get("DB_ENGINE", "django.db.backends.mysql"),
        'NAME': os.environ.get("DB_NAME", "yaayess_db"),
        'USER': os.environ.get("DB_USER", "root"),
        'PASSWORD': os.environ.get("DB_PASSWORD", ""),
        'HOST': os.environ.get("DB_HOST", "localhost"),
        'PORT': os.environ.get("DB_PORT", "3306"),
    }
}

# Fichiers statiques
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Médias
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Sécurité (mode production)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG


# ----------------------------------
# Applications installées (exemple minimal)
# ----------------------------------
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

# ----------------------------------
# Middleware
# ----------------------------------
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

AUTH_USER_MODEL = 'accounts.CustomUser'


ROOT_URLCONF = 'yaayess.urls'

# ----------------------------------
# Templates
# ----------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # adapte selon ta structure
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


# ----------------------------------
# Password validation (optionnel)
# ----------------------------------
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

# ----------------------------------
# Internationalisation
# ----------------------------------
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Dakar'
USE_I18N = True
USE_TZ = True

# ----------------------------------
# Static files (CSS, JS, Images)
# ----------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Optionnel : chemins supplémentaires pour staticfiles
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # si tu as un dossier static en développement
]

# ----------------------------------
# Media files (uploads utilisateur)
# ----------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ----------------------------------
# Sécurité supplémentaire (optionnel)
# ----------------------------------
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# ----------------------------------
# Default primary key field type
# ----------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# PayDunya Sandbox API Keys


PAYDUNYA_KEYS = {
    "master_key": os.getenv("PAYDUNYA_MASTER_KEY"),
    "private_key": os.getenv("PAYDUNYA_PRIVATE_KEY"),
    "public_key": os.getenv("PAYDUNYA_PUBLIC_KEY"),
    "token": os.getenv("PAYDUNYA_TOKEN"),
}



"""