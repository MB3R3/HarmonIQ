"""
Django settings for config project.

Configuration is environment-driven so the same code runs locally (SQLite,
DEBUG=True) and in production on Google Cloud Run (PostgreSQL, DEBUG=False).
Nothing production-specific is hardcoded here: hostnames, frontend origins
and Spotify credentials all come from environment variables. See
.env.example for the full list.
"""
import os
import secrets

from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlparse

from dotenv import load_dotenv


load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


TRUTHY_VALUES = {"1", "true", "t", "yes", "y", "on"}


def env(name, default=None):
    """Read an environment variable, treating empty strings as unset."""

    value = os.getenv(name)

    if value is None or not value.strip():
        return default

    return value.strip()


def env_bool(name, default=False):
    """Read a boolean environment variable (1/true/yes/on are truthy)."""

    value = env(name)

    if value is None:
        return default

    return value.lower() in TRUTHY_VALUES


def env_list(name, default=()):
    """Read a comma-separated environment variable into a list."""

    value = env(name)

    if value is None:
        return list(default)

    return [item.strip() for item in value.split(",") if item.strip()]


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# In production this MUST be supplied via the SECRET_KEY environment variable.
SECRET_KEY = env("SECRET_KEY", "")

# SECURITY WARNING: don't run with debug turned on in production!
# Local development stays on DEBUG=True unless explicitly overridden.
DEBUG = env_bool("DEBUG", default=True)

# Development defaults keep `runserver` working with no .env file present.
# Production must set ALLOWED_HOSTS explicitly (e.g. the Cloud Run host).
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", default=[])
DEFAULT_ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
if not ALLOWED_HOSTS and DEBUG:
    ALLOWED_HOSTS = DEFAULT_ALLOWED_HOSTS

if not SECRET_KEY and DEBUG:
    # Dev-only convenience so a fresh clone runs without a .env file. The key
    # is regenerated on every process start (sessions do not survive a
    # restart) and is never used when DEBUG is off.
    SECRET_KEY = (
        "dev-only-ephemeral-key-" + secrets.token_urlsafe(50)
    )

if not DEBUG:
    from django.core.exceptions import ImproperlyConfigured

    if not SECRET_KEY:
        raise ImproperlyConfigured(
            "SECRET_KEY must be set in the environment when DEBUG=False."
        )

    if "django-insecure-" in SECRET_KEY:
        raise ImproperlyConfigured(
            "SECRET_KEY still looks like a development key. Set a unique "
            "SECRET_KEY in the environment before running with DEBUG=False."
        )

    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured(
            "ALLOWED_HOSTS must be set in the environment when DEBUG=False."
        )


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',
    'recommendations',
    'music',

    # Third party
    "rest_framework",
    "corsheaders",

    # # Local
    # "users",
    # "music",
    # "recommendations",
]

# WhiteNoise serves collected static files from the app itself in production
# (no separate static host). In development the normal staticfiles app keeps
# serving assets, so WhiteNoise is only enabled when DEBUG is off.
WHITENOISE_MIDDLEWARE = (
    ["whitenoise.middleware.WhiteNoiseMiddleware"] if not DEBUG else []
)

MIDDLEWARE = [

    "corsheaders.middleware.CorsMiddleware",


    'django.middleware.security.SecurityMiddleware',
    *WHITENOISE_MIDDLEWARE,
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = False
# The React app (Vercel in production, localhost:5173 in development) is a
# different origin, and it sends cross-origin requests with credentials so the
# Django session cookie (SessionAuthentication) is included.
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173"] if DEBUG else [],
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

def database_from_url(database_url):
    """Build a PostgreSQL DATABASES entry from a DATABASE_URL value.

    Supports ``postgres://`` and ``postgresql://`` URLs, e.g.
    ``postgresql://USER:PASSWORD@HOST:PORT/DATABASE``. Extra query parameters
    (``sslmode``, ``connect_timeout``, ...) are passed straight through to the
    driver, which is what Cloud SQL will need for TLS connections.
    """

    parsed = urlparse(database_url)

    if parsed.scheme not in ("postgres", "postgresql", "psql"):
        raise ValueError(
            "DATABASE_URL must start with postgres:// or postgresql:// "
            f"(got {parsed.scheme!r})."
        )

    options = dict(parse_qsl(parsed.query))

    if not parsed.hostname:
        raise ValueError("DATABASE_URL is missing a host.")

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parsed.path.lstrip("/")),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname,
        "PORT": str(parsed.port or ""),
        "CONN_MAX_AGE": int(env("DB_CONN_MAX_AGE", "60")),
        "OPTIONS": options,
    }


DATABASE_URL = env("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {"default": database_from_url(DATABASE_URL)}
else:
    # Local development keeps working on SQLite without PostgreSQL installed.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
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

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# After a successful login, send users somewhere valid instead of
# Django's default broken /accounts/profile/.
LOGIN_REDIRECT_URL = "/api/recommendations/discover/"

# Django 4+ validates the Origin header of every unsafe request against this
# list (separate from CORS). Without it, cross-origin POSTs fail with
# "Origin checking failed" even when the CSRF header/cookie match.
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ] if DEBUG else [],
)

# The React app (Vercel in production) and the Django API (Cloud Run) are
# different sites, so Django's default SameSite=Lax cookies would NOT be sent
# on the frontend's cross-origin fetch requests. SameSite=None is therefore
# required in both environments for SessionAuthentication to keep working;
# CSRF is still fully enforced via the X-CSRFToken header.
#
# SameSite=None cookies are only sent over HTTPS by browsers, so the Secure
# flags stay on in development exactly as before, and local HTTP keeps working
# through the same configuration as before this change.
SESSION_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SAMESITE = "None"

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

if not DEBUG:
    WHITENOISE_MAX_AGE = 60 * 60 * 24 * 365

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Spotify OAuth
SPOTIFY_CLIENT_ID = env("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = env("SPOTIFY_CLIENT_SECRET")

# Production supplies the Cloud Run callback URL here; the local fallback keeps
# `runserver` usable without a .env file.
SPOTIFY_REDIRECT_URI = env(
    "SPOTIFY_REDIRECT_URI",
    "http://127.0.0.1:8000/api/users/spotify/callback/" if DEBUG else "",
)

# Where the React SPA lives. The Spotify OAuth callback bounces the browser
# back here after linking a Spotify account.
FRONTEND_URL = env(
    "FRONTEND_URL",
    "http://localhost:5173" if DEBUG else "",
).rstrip("/")


if not DEBUG:
    # Cloud Run terminates TLS at its HTTPS proxy and forwards plain HTTP to
    # the container, so Django must trust X-Forwarded-Proto to decide whether
    # a request arrived over HTTPS (affects secure cookies, redirects and HSTS).
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=True)

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    SECURE_HSTS_SECONDS = int(env("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    SECURE_CONTENT_TYPE_NOSNIFF = True

    X_FRAME_OPTIONS = "DENY"
