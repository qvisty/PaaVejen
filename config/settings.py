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
    "apps.notifications",
    "apps.audit",
    "apps.moderation",
    "apps.payments",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        # Uden manifest, så udvikling og tests virker uden collectstatic.
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Sikkerhed i drift. Slås til, når DEBUG er slået fra.
if not DEBUG:
    CSRF_TRUSTED_ORIGINS = [
        origin for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if origin
    ]
    SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "1") == "1"
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# E mail, jf. PRD afsnit 22. Konsol i udvikling, SMTP via miljøvariabler i drift.
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.environ.get("DJANGO_EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("DJANGO_EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("DJANGO_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("DJANGO_EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("DJANGO_EMAIL_USE_TLS", "1") == "1"
DEFAULT_FROM_EMAIL = os.environ.get("DJANGO_DEFAULT_FROM_EMAIL", "PåVejen <noreply@paavejen.dk>")

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
    # Basis URL til links i notifikationsmails.
    "BASE_URL": os.environ.get("PAAVEJEN_BASE_URL", "http://127.0.0.1:8000"),
    # Platformens andel af transportprisen, jf. PRD afsnit 13.
    "PLATFORM_FEE_PERCENT": 15,
}
