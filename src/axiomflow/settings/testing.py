"""Testing settings.

Provides configuration for running the test suite with an in-memory SQLite
backend and local-memory caching.

Attributes:
    DEBUG (bool): Enables debug mode during tests.
    DATABASES (dict): In-memory SQLite database configuration.
    CACHES (dict): Local-memory cache backend.
"""

from .base import INSTALLED_APPS, MIDDLEWARE  # noqa: F401

DEBUG = True

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
