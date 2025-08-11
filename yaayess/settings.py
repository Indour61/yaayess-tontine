import os
import environ
from pathlib import Path


env = environ.Env()
environ.Env.read_env()

DJANGO_ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
# ----------------------------------
# BASE DIR
# ----------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------------------------
# Initialise django-environ
# ----------------------------------
env = environ.Env(
    # Valeurs par défaut
    DEBUG=(bool, False)
)

# Lis le fichier .env à la racine du projet
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# ----------------------------------
# Sécurité
# ----------------------------------
SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env('DEBUG')
#ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS')
#ALLOWED_HOSTS = ['168.231.117.6', 'www.yaayess.com', 'yaayess.com']

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
# Base de données MySQL
# ----------------------------------
DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE', default='django.db.backends.mysql'),
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'OPTIONS': {
            'init_command': env('DB_INIT_COMMAND', default="SET sql_mode='STRICT_TRANS_TABLES'"),
            'charset': env('DB_CHARSET', default='utf8mb4'),
        },
    }
}

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



