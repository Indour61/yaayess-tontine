import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Charge .env le plus tôt possible (et écrase les valeurs vides du système si besoin)
load_dotenv(BASE_DIR / ".env", override=True)

# ---- ensuite seulement, lis tes variables ----
SECRET_KEY = os.environ["SECRET_KEY"]                 # déjà dans ton .env
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")          # ⬅️ lira bien la valeur du .env
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY manquante. Vérifie .env ou les variables d'environnement.")


CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]
"""
CSRF_TRUSTED_ORIGINS = [
    "https://127.0.0.1:8000",
    "https://localhost:8000",
    "https://yaayess.com",
]
"""
# ----------------------------------------------------
# 🗄 DATABASE - Version sécurisée
# ----------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "OPTIONS": {"sslmode": os.getenv("DB_SSLMODE", "prefer")},
    }
}
# PROD security (activés automatiquement quand DEBUG=False)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
"""
if DEBUG:
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False
    CSRF_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_USE_SESSIONS = True
else:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
"""
# ----------------------------------------------------
# 🌍 OPENAI
# ----------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ----------------------------------------------------
# 💳 PAYDUNYA
# ----------------------------------------------------
# --- PayDunya ---
PAYDUNYA = {
    "MASTER_KEY": os.getenv("PAYDUNYA_MASTER_KEY", ""),
    "MODE": os.getenv("PAYDUNYA_MODE", "test").lower(),  # "test" | "live"
    "TEST": {
        "PUBLIC_KEY": os.getenv("PAYDUNYA_TEST_PUBLIC_KEY", ""),
        "PRIVATE_KEY": os.getenv("PAYDUNYA_TEST_PRIVATE_KEY", ""),
        "TOKEN": os.getenv("PAYDUNYA_TEST_TOKEN", ""),
        "BASE_URL": "https://app.paydunya.com/sandbox-api/v1",
        "CHECKOUT_URL": "https://paydunya.com/sandbox-checkout/invoice",
    },
    "LIVE": {
        "PUBLIC_KEY": os.getenv("PAYDUNYA_LIVE_PUBLIC_KEY", ""),
        "PRIVATE_KEY": os.getenv("PAYDUNYA_LIVE_PRIVATE_KEY", ""),
        "TOKEN": os.getenv("PAYDUNYA_LIVE_TOKEN", ""),
        "BASE_URL": "https://app.paydunya.com/api/v1",
        "CHECKOUT_URL": "https://paydunya.com/checkout/invoice",
    },
    "STORE": {
        "NAME": os.getenv("PAYDUNYA_STORE_NAME", "YaayESS"),
        "TAGLINE": os.getenv("PAYDUNYA_STORE_TAGLINE", ""),
        "URL": os.getenv("PAYDUNYA_STORE_URL", ""),
    },
    "FEES": {
        "RATE": float(os.getenv("PAYDUNYA_FEE_RATE", "0.025")),
        "FIXED": int(float(os.getenv("PAYDUNYA_FEE_FIXED", "75"))),
    },
}

def get_paydunya_keys():
    mode = PAYDUNYA["MODE"]
    assert mode in ("test", "live")
    keys = PAYDUNYA["TEST"] if mode == "test" else PAYDUNYA["LIVE"]
    return {
        "MASTER_KEY": PAYDUNYA["MASTER_KEY"],
        "PUBLIC_KEY": keys["PUBLIC_KEY"],
        "PRIVATE_KEY": keys["PRIVATE_KEY"],
        "TOKEN": keys["TOKEN"],
        "BASE_URL": keys["BASE_URL"],
        "CHECKOUT_URL": keys["CHECKOUT_URL"],
        "MODE": mode,
    }

"""
PAYDUNYA_MODE = os.environ.get("PAYDUNYA_MODE", "test").lower()
PAYDUNYA_MASTER_KEY = os.environ.get("PAYDUNYA_MASTER_KEY")

if PAYDUNYA_MODE == "live":
    PAYDUNYA_PUBLIC_KEY = os.environ.get("PAYDUNYA_LIVE_PUBLIC_KEY")
    PAYDUNYA_PRIVATE_KEY = os.environ.get("PAYDUNYA_LIVE_PRIVATE_KEY")
    PAYDUNYA_TOKEN = os.environ.get("PAYDUNYA_LIVE_TOKEN")
else:
    PAYDUNYA_PUBLIC_KEY = os.environ.get("PAYDUNYA_TEST_PUBLIC_KEY")
    PAYDUNYA_PRIVATE_KEY = os.environ.get("PAYDUNYA_TEST_PRIVATE_KEY")
    PAYDUNYA_TOKEN = os.environ.get("PAYDUNYA_TEST_TOKEN")

PAYDUNYA = {
    "master_key": PAYDUNYA_MASTER_KEY,
    "private_key": PAYDUNYA_PRIVATE_KEY,
    "public_key": PAYDUNYA_PUBLIC_KEY,
    "token": PAYDUNYA_TOKEN,
    "sandbox": PAYDUNYA_MODE != "live",
    "store_name": os.environ.get("PAYDUNYA_STORE_NAME", "YaayESS"),
    "store_tagline": os.environ.get("PAYDUNYA_STORE_TAGLINE", "Plateforme de gestion financière"),
    "website_url": os.environ.get("PAYDUNYA_STORE_URL", "https://yaayess.com"),
}
"""

# settings.py
PAYDUNYA_FEE_RATE = float(os.getenv("PAYDUNYA_FEE_RATE", "0.025"))
PAYDUNYA_FEE_FIXED = int(os.getenv("PAYDUNYA_FEE_FIXED", "75"))

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
    'assistant_ai',
    'cotisationtontine',
    'epargnecredit',
    'legal',
    'rest_framework',
    'widget_tweaks',

    # Outils
    'whitenoise.runserver_nostatic',
    'sslserver',
]

TERMS_VERSION = "v1.0-2025-09-07"

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
    "legal.middleware.TermsGateMiddleware"
]

ROOT_URLCONF = 'yaayess.urls'
WSGI_APPLICATION = 'yaayess.wsgi.application'

# Templates : vérifie bien l’entrée DIRS → "templates/"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],   # ✅ important pour templates/assistant_ai/...
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.csrf",  # ✅
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ----------------------------------------------------
# ✉️ EMAIL CONFIG - Version sécurisée
# ----------------------------------------------------
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.environ["EMAIL_HOST_USER"]        # Doit être défini
EMAIL_HOST_PASSWORD = os.environ["EMAIL_HOST_PASSWORD"] # Doit être défini


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
    'accounts.backends.NomBackend',
]
"""
AUTHENTICATION_BACKENDS = [
    'accounts.backend.NomBackend',
    'django.contrib.auth.backends.ModelBackend',  # fallback par défaut
]
"""


# settings.py
LOGIN_URL = '/accounts/login/'          # redirection pour utilisateurs non connectés
LOGIN_REDIRECT_URL = '/groups/'         # redirection après login réussi

# Uploads audio (sécu & confort)
DATA_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024  # 15 Mo
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 Mo


# Dev only: servir /media
if DEBUG:
    from django.conf.urls.static import static
    from django.conf import settings as _s
    urlpatterns = []
    urlpatterns += static(_s.MEDIA_URL, document_root=_s.MEDIA_ROOT)
