"""Development settings.

Extends base settings with debugging helpers, SQLite fallback, and local-memory
caching.

Attributes:
    DEBUG (bool): Enables Django debug mode.
    DATABASES (dict): Database configuration using ``DATABASE_URL`` or SQLite.
    CACHES (dict): Local-memory cache backend.
"""

from importlib import util

from .base import BASE_DIR, INSTALLED_APPS, MIDDLEWARE, env

DEBUG = True

DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

if util.find_spec("debug_toolbar"):
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
