"""Production settings.

Configures the application for deployed environments. Debugging is disabled and
all critical values are pulled from environment variables.

Attributes:
    DEBUG (bool): Always ``False`` in production.
    ALLOWED_HOSTS (list[str]): Allowed hostnames from ``DJANGO_ALLOWED_HOSTS``.
    DATABASES (dict): Database configuration from ``DATABASE_URL``.
    CACHES (dict): Cache configuration from ``CACHE_URL``.
    THIRD_PARTY_API_KEY (str): Example external service credential.
"""

from .base import env

DEBUG = False

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

DATABASES = {"default": env.db("DATABASE_URL")}

CACHES = {"default": env.cache("CACHE_URL", default="locmemcache://")}

THIRD_PARTY_API_KEY = env("THIRD_PARTY_API_KEY", default="")
