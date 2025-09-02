import importlib
import os
import sys
from importlib import util
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")


@pytest.mark.parametrize("debug_toolbar_available", [True, False])
def test_development_sqlite_fallback_and_debug_toolbar(
    monkeypatch, debug_toolbar_available
):
    """Development uses SQLite by default and integrates debug_toolbar if present."""
    base = importlib.import_module("axiomflow.settings.base")
    apps_before = base.INSTALLED_APPS.copy()
    middleware_before = base.MIDDLEWARE.copy()
    monkeypatch.delenv("DATABASE_URL", raising=False)

    module_name = "axiomflow.settings.development"
    if module_name in sys.modules:
        del sys.modules[module_name]

    monkeypatch.setattr(
        util,
        "find_spec",
        lambda name: (
            object() if debug_toolbar_available and name == "debug_toolbar" else None
        ),
    )

    module = importlib.import_module(module_name)

    db = module.DATABASES["default"]
    assert db["ENGINE"] == "django.db.backends.sqlite3"
    assert db["NAME"].endswith("db.sqlite3")

    if debug_toolbar_available:
        assert "debug_toolbar" in module.INSTALLED_APPS
        assert module.MIDDLEWARE[0] == "debug_toolbar.middleware.DebugToolbarMiddleware"
    else:
        assert "debug_toolbar" not in module.INSTALLED_APPS
        assert module.MIDDLEWARE[0] != "debug_toolbar.middleware.DebugToolbarMiddleware"

    base.INSTALLED_APPS[:] = apps_before
    base.MIDDLEWARE[:] = middleware_before


def test_production_environment(monkeypatch):
    """Production derives configuration exclusively from environment variables."""
    module_name = "axiomflow.settings.production"
    for name, value in {
        "DJANGO_SECRET_KEY": "prod-secret",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/db",
        "DJANGO_ALLOWED_HOSTS": "example.com,api.example.com",
        "CACHE_URL": "redis://localhost:6379/1",
    }.items():
        monkeypatch.setenv(name, value)

    if module_name in sys.modules:
        del sys.modules[module_name]

    module = importlib.import_module(module_name)

    assert module.DEBUG is False
    assert module.ALLOWED_HOSTS == ["example.com", "api.example.com"]

    cache = module.CACHES["default"]
    assert cache["BACKEND"] == "django.core.cache.backends.redis.RedisCache"
    assert cache["LOCATION"] == "redis://localhost:6379/1"


def test_testing_environment(monkeypatch):
    """Testing uses in-memory SQLite and a local-memory cache backend."""
    module_name = "axiomflow.settings.testing"
    for name, value in {
        "DJANGO_SECRET_KEY": "test-secret",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/db",
    }.items():
        monkeypatch.setenv(name, value)

    if module_name in sys.modules:
        del sys.modules[module_name]

    module = importlib.import_module(module_name)

    db = module.DATABASES["default"]
    assert db["ENGINE"] == "django.db.backends.sqlite3"
    assert db["NAME"] == ":memory:"

    cache = module.CACHES["default"]
    assert cache["BACKEND"] == "django.core.cache.backends.locmem.LocMemCache"
