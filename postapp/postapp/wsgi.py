"""
WSGI config for postknob project.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "postapp.settings.prod")
application = get_wsgi_application()
