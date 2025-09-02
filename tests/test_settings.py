import importlib
import os
import sys
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")

from axiomflow.settings import base


def test_auth_settings_defined():
    assert base.AUTH_USER_MODEL == os.getenv("AUTH_USER_MODEL", "auth.User")
    assert base.AUTHENTICATION_BACKENDS == ["django.contrib.auth.backends.ModelBackend"]


def test_role_permissions_hierarchy():
    perms = base.ROLE_PERMISSIONS
    assert perms[base.Role.OWNER] == set(base.Permission)
    assert perms[base.Role.VIEWER] == {base.Permission.VIEW_WORKFLOWS}
    assert perms[base.Role.RUNNER] >= {
        base.Permission.RUN_WORKFLOWS,
        base.Permission.VIEW_WORKFLOWS,
    }
    assert perms[base.Role.EDITOR] >= {
        base.Permission.MANAGE_WORKFLOWS,
        base.Permission.RUN_WORKFLOWS,
        base.Permission.VIEW_WORKFLOWS,
    }
    assert perms[base.Role.ADMIN] >= {
        base.Permission.MANAGE_USERS,
        base.Permission.MANAGE_WORKFLOWS,
        base.Permission.RUN_WORKFLOWS,
        base.Permission.VIEW_WORKFLOWS,
    }
    for role, permissions in perms.items():
        assert permissions <= perms[base.Role.OWNER]


def test_session_cookie_secure_env(monkeypatch):
    module = importlib.import_module("axiomflow.settings.base")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "False")
    importlib.reload(module)
    assert module.SESSION_COOKIE_SECURE is False
    monkeypatch.delenv("SESSION_COOKIE_SECURE", raising=False)
    importlib.reload(module)
    assert module.SESSION_COOKIE_SECURE is True


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://user@localhost:5432/db",
        "postgresql://:pass@localhost:5432/db",
        "postgresql://user:pass@localhost",
    ],
)
def test_invalid_database_url_raises(monkeypatch, url):
    module = importlib.import_module("axiomflow.settings.base")
    monkeypatch.setenv("DATABASE_URL", url)
    with pytest.raises(ImproperlyConfigured):
        importlib.reload(module)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    importlib.reload(module)


def test_cache_backend_redis(monkeypatch):
    module = importlib.import_module("axiomflow.settings.base")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    importlib.reload(module)
    cache = module.CACHES["default"]
    assert cache["BACKEND"] == "django.core.cache.backends.redis.RedisCache"
    assert cache["LOCATION"] == "redis://localhost:6379/1"
    monkeypatch.delenv("REDIS_URL", raising=False)
    importlib.reload(module)


def test_cache_backend_locmem(monkeypatch):
    module = importlib.import_module("axiomflow.settings.base")
    monkeypatch.delenv("REDIS_URL", raising=False)
    importlib.reload(module)
    cache = module.CACHES["default"]
    assert cache["BACKEND"] == "django.core.cache.backends.locmem.LocMemCache"
