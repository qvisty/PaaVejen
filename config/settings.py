"""
Django settings for PåVejen.

Første prototype, jf. PRD afsnit 40 og 58.
SQLite som database. PostgreSQL når produktet bliver multiplayer.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-paavejen-prototype-key-skift-foer-drift",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # PåVejen apps
    "apps.core",
    "apps.accounts",
    "apps.trips",
    "apps.transport",
    "apps.matching",
    "apps.bookings",
    "apps.messaging",
    "apps.ratings",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "da"

TIME_ZONE = "Europe/Copenhagen"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "home"

# PåVejen domæneparametre, jf. PRD afsnit 12 og 18.
PAAVEJEN = {
    # Prisforslag: grundbeløb + omvej + tid + størrelse.
    "PRICE_BASE": 30,            # kr.
    "PRICE_PER_DETOUR_KM": 2,    # kr. pr. ekstra kilometer
    "PRICE_PER_DETOUR_MIN": 1,   # kr. pr. ekstra minut
    "PRICE_SIZE_SUPPLEMENT": {   # kr. pr. størrelseskategori
        "small_bag": 0,
        "moving_box": 10,
        "several_boxes": 20,
        "trunk": 30,
        "station_wagon": 40,
        "van": 50,
        "trailer": 60,
    },
    # Maksimal accepteret vareværdi i prototypen.
    "MAX_ITEM_VALUE": 5000,      # kr.
    # Geografisk prefilter: hvor langt fra ruten et punkt maksimalt må ligge.
    "MAX_CORRIDOR_KM": 25,
    # Standard maksimal omvej hvis chaufføren ikke har angivet en.
    "DEFAULT_MAX_DETOUR_MINUTES": 30,
}
