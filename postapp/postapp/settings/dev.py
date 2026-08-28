"""Development settings — extends base."""
from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Show emails in console during development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Use simpler static files storage in dev
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Django Debug Toolbar (optional — install separately)
try:
    import debug_toolbar  # noqa: F401
    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
    INTERNAL_IPS = ["127.0.0.1"]
except ImportError:
    pass

# Relaxed CORS for local frontend dev
CORS_ALLOW_ALL_ORIGINS = True
