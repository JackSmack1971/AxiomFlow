from __future__ import annotations

import base64
import json
import shutil
from importlib import util
from pathlib import Path
from typing import Sequence

import yaml
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

REPO_ROOT = Path(__file__).resolve().parents[3]
POLICY_FILE = REPO_ROOT / "configs" / "policies" / "allowed_scopes.yaml"
REGISTRY_FILE = REPO_ROOT / "configs" / "adapters.yaml"
INSTALL_BASE = REPO_ROOT / "adapters"


def _verify_manifest(manifest: dict) -> dict:
    payload = manifest.get("payload")
    signature_b64 = manifest.get("signature")
    public_key_b64 = manifest.get("public_key")
    if payload is None or signature_b64 is None or public_key_b64 is None:
        raise ValueError("Manifest missing required fields")
    signature = base64.b64decode(signature_b64)
    public_key = base64.b64decode(public_key_b64)
    message = json.dumps(payload, sort_keys=True).encode()
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
    except InvalidSignature as exc:  # pragma: no cover - edge case
        raise ValueError("Invalid manifest signature") from exc
    return payload


def _validate_scopes(permissions: Sequence[str]) -> None:
    allowed_data = yaml.safe_load(POLICY_FILE.read_text()) or {}
    allowed_scopes = set(allowed_data.get("allowed_scopes", []))
    if not set(permissions).issubset(allowed_scopes):
        raise ValueError("Requested permissions exceed policy")


def _register_adapter(project_id: str, adapter_id: str) -> None:
    registry = {}
    if REGISTRY_FILE.exists():
        registry = yaml.safe_load(REGISTRY_FILE.read_text()) or {}
    adapters = registry.get(project_id, [])
    if adapter_id not in adapters:
        adapters.append(adapter_id)
    registry[project_id] = adapters
    REGISTRY_FILE.write_text(yaml.safe_dump(registry))


def _run_health_check(adapter_path: Path) -> bool:
    init_file = adapter_path / "__init__.py"
    if not init_file.exists():
        return False
    spec = util.spec_from_file_location(f"adapter_{adapter_path.name}", init_file)
    if spec is None or spec.loader is None:
        return False
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    health = getattr(module, "health_check", None)
    if not callable(health):
        return False
    return bool(health())


def configure_adapter(
    adapter_id: str,
    manifest_path: Path,
    permissions: Sequence[str],
    project_id: str,
) -> dict:
    """Configure and install an adapter.

    Args:
        adapter_id: Identifier in the form org/name@version.
        manifest_path: Path to the signed manifest file.
        permissions: Requested permission scopes.
        project_id: Target project identifier.

    Returns:
        Mapping containing installation status and health check result.

    Raises:
        ValueError: If manifest verification, scope validation, or health check fails.
    """

    manifest = json.loads(Path(manifest_path).read_text())
    payload = _verify_manifest(manifest)
    _validate_scopes(permissions)

    safe_name = adapter_id.replace("/", "_")
    dest = INSTALL_BASE / project_id / safe_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(payload["source"], dest, dirs_exist_ok=True)

    _register_adapter(project_id, adapter_id)

    if not _run_health_check(dest):
        raise ValueError("Adapter health check failed")

    return {"installation_status": "success", "health_check_result": True}
