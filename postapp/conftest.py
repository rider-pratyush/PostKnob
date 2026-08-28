"""
pytest configuration and shared fixtures for PostKnob tests.
"""
import django
import pytest
from django.conf import settings


def pytest_configure():
    settings.DJANGO_SETTINGS_MODULE = "postapp.settings.dev"


@pytest.fixture(autouse=True)
def reset_db_sequences(db):
    """Ensure a clean DB state per test (handled by pytest-django transactional tests)."""
    pass
