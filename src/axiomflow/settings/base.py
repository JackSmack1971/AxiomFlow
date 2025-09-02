"""Base Django settings.

Environment variables are loaded using ``django-environ``. These settings are
shared across all environments. Database and cache connections rely on
``DATABASE_URL`` and ``REDIS_URL`` environment variables, respectively.

Attributes:
    env (environ.Env): Environment helper for reading variables.
    BASE_DIR (Path): Root directory of the project.
    SECRET_KEY (str): Secret key from ``DJANGO_SECRET_KEY``.
    DATABASES (dict): Database configuration derived from ``DATABASE_URL``.
    CACHES (dict): Cache configuration derived from ``REDIS_URL`` with a
        fallback to local memory.
    INSTALLED_APPS (list[str]): Core Django applications.
    MIDDLEWARE (list[str]): Default middleware stack.
    TEMPLATES (list[dict]): Template engine configuration.
    LOGGING (dict): Structured logging with correlation IDs.

Structured logging emits JSON to stdout for container compatibility. The
``CorrelationIdMiddleware`` reads an ``X-Request-ID`` header or generates a UUID
and stores it in a context variable. ``CorrelationIdFilter`` attaches this value
to each log record so requests can be traced across services.
"""

from enum import StrEnum
from pathlib import Path
from urllib.parse import urlparse

import environ
from django.core.exceptions import ImproperlyConfigured
from pydantic import BaseModel, PostgresDsn, ValidationError, model_validator

env = environ.Env()
environ.Env.read_env()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = env("DJANGO_SECRET_KEY")


class DatabaseURL(BaseModel):
    """Validate the ``DATABASE_URL`` environment variable.

    Ensures the connection string includes user, password, host, and
    database name using the PostgreSQL DSN format, for example::

        postgresql://user:pass@host:5432/db
    """

    url: PostgresDsn

    @model_validator(mode="after")
    def ensure_components(self) -> "DatabaseURL":
        parsed = urlparse(str(self.url))
        if not all(
            [
                parsed.username,
                parsed.password,
                parsed.hostname,
                parsed.path.lstrip("/"),
            ]
        ):
            raise ValueError(
                "DATABASE_URL must include user, password, host, and database name"
            )
        return self


try:
    _db_settings = DatabaseURL(url=env("DATABASE_URL"))
except ValidationError as exc:  # pragma: no cover - configuration validation
    raise ImproperlyConfigured("Invalid DATABASE_URL") from exc

_parsed_db_url = urlparse(str(_db_settings.url))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _parsed_db_url.path.lstrip("/"),
        "USER": _parsed_db_url.username,
        "PASSWORD": _parsed_db_url.password,
        "HOST": _parsed_db_url.hostname,
        "PORT": str(_parsed_db_url.port or 5432),
    }
}
"""Database configuration derived from ``DATABASE_URL``.

The environment variable must be a fully qualified PostgreSQL connection
string including user, password, host, port, and database name.
"""


_redis_url = env.str("REDIS_URL", default="")

if _redis_url:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": _redis_url,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
"""Cache backend configuration.

If ``REDIS_URL`` is provided, a Redis cache backend is used. Otherwise, a
local-memory cache backend is configured.
"""

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# Authentication configuration
AUTH_USER_MODEL = env.str("AUTH_USER_MODEL", default="auth.User")
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "axiomflow.middleware.CorrelationIdMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

# Session and CSRF security settings
SESSION_COOKIE_AGE = env.int("SESSION_COOKIE_AGE", default=60 * 60 * 24)
SESSION_EXPIRE_AT_BROWSER_CLOSE = env.bool(
    "SESSION_EXPIRE_AT_BROWSER_CLOSE", default=False
)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)
SESSION_COOKIE_HTTPONLY = env.bool("SESSION_COOKIE_HTTPONLY", default=True)
SESSION_COOKIE_SAMESITE = env.str("SESSION_COOKIE_SAMESITE", default="Lax")

CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)
CSRF_COOKIE_HTTPONLY = env.bool("CSRF_COOKIE_HTTPONLY", default=True)
CSRF_COOKIE_SAMESITE = env.str("CSRF_COOKIE_SAMESITE", default="Lax")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])


# Structured logging configuration.

# The ``CorrelationIdMiddleware`` extracts an ``X-Request-ID`` header from each
# incoming HTTP request, generating a UUID when the header is absent. The value
# is stored in a context variable so that :class:`axiomflow.logging.CorrelationIdFilter`
# can attach it to every log record as ``correlation_id``. Logs are rendered by
# ``JsonFormatter`` and emitted to stdout in JSON format, ensuring container
# compatibility and request tracing across services.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"correlation_id": {"()": "axiomflow.logging.CorrelationIdFilter"}},
    "formatters": {"json": {"()": "axiomflow.logging.JsonFormatter"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "json",
            "filters": ["correlation_id"],
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}


class Permission(StrEnum):
    """Permission categories for role-based access control.

    Attributes:
        MANAGE_USERS: Create, update, and delete user accounts.
        MANAGE_WORKFLOWS: Create and modify workflow definitions.
        RUN_WORKFLOWS: Start and control workflow executions.
        VIEW_WORKFLOWS: Read workflows, runs, and artifacts.
    """

    MANAGE_USERS = "manage_users"
    MANAGE_WORKFLOWS = "manage_workflows"
    RUN_WORKFLOWS = "run_workflows"
    VIEW_WORKFLOWS = "view_workflows"


class Role(StrEnum):
    """RBAC roles available within the platform.

    The roles form a hierarchy where each level inherits permissions from the
    levels below it.

    Attributes:
        OWNER: Full control over the system and all workspaces.
        ADMIN: Manage a workspace and its user membership.
        EDITOR: Modify workflow definitions and configuration.
        RUNNER: Execute existing workflows without modification rights.
        VIEWER: Read-only access to workflows and execution results.
    """

    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    RUNNER = "runner"
    VIEWER = "viewer"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.OWNER: set(Permission),
    Role.ADMIN: {
        Permission.MANAGE_USERS,
        Permission.MANAGE_WORKFLOWS,
        Permission.RUN_WORKFLOWS,
        Permission.VIEW_WORKFLOWS,
    },
    Role.EDITOR: {
        Permission.MANAGE_WORKFLOWS,
        Permission.RUN_WORKFLOWS,
        Permission.VIEW_WORKFLOWS,
    },
    Role.RUNNER: {
        Permission.RUN_WORKFLOWS,
        Permission.VIEW_WORKFLOWS,
    },
    Role.VIEWER: {Permission.VIEW_WORKFLOWS},
}
"""Mapping of RBAC roles to their permitted actions."""
