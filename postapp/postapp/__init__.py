"""PostKnob Django project __init__ — loads Celery app."""
from .celery import app as celery_app

__all__ = ("celery_app",)
