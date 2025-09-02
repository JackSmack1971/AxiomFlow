import importlib
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")

from axiomflow.settings import base


def test_auth_settings_defined():
    assert base.AUTH_USER_MODEL == os.getenv("AUTH_USER_MODEL", "auth.User")
    assert base.AUTHENTICATION_BACKENDS == ["django.contrib.auth.backends.ModelBackend"]


def test_role_permissions_hierarchy():
    perms = base.ROLE_PERMISSIONS
    assert perms[base.Role.VIEWER] == {base.Permission.VIEW_WORKFLOWS}
    assert perms[base.Role.RUNNER] >= perms[base.Role.VIEWER]
    assert perms[base.Role.EDITOR] >= perms[base.Role.RUNNER]
    assert perms[base.Role.ADMIN] >= perms[base.Role.EDITOR]
    assert perms[base.Role.OWNER] >= perms[base.Role.ADMIN]


def test_session_cookie_secure_env(monkeypatch):
    module = importlib.import_module("axiomflow.settings.base")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "False")
    importlib.reload(module)
    assert module.SESSION_COOKIE_SECURE is False
    monkeypatch.delenv("SESSION_COOKIE_SECURE", raising=False)
    importlib.reload(module)
    assert module.SESSION_COOKIE_SECURE is True
