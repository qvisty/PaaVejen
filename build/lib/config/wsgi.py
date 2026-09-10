import logging
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()

# I flygtige miljøer som Vercels serverless funktioner migreres den
# lokale SQLite database automatisk ved kold start, så demoen altid
# starter med et brugbart skema.
if os.environ.get("PAAVEJEN_AUTO_MIGRATE") == "1" or (
    os.environ.get("VERCEL") and not os.environ.get("DATABASE_URL")
):
    try:
        from django.core.management import call_command

        call_command("migrate", interactive=False, verbosity=0)
    except Exception:
        logging.getLogger(__name__).exception("Automatisk migrering fejlede")

# Vercels Python runtime leder efter variablen "app".
app = application
