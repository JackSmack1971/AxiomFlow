import base64
import json
import sys
from pathlib import Path

import pytest
import yaml
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from axiomflow.adapters import configure_adapter


def _create_adapter(tmp_path: Path) -> Path:
    adapter_dir = tmp_path / "sample_adapter"
    adapter_dir.mkdir()
    adapter_dir.joinpath("__init__.py").write_text(
        "def health_check():\n    return True\n"
    )
    return adapter_dir


def _create_manifest(tmp_path: Path, adapter_dir: Path) -> Path:
    key = Ed25519PrivateKey.generate()
    public_key = key.public_key()
    payload = {"source": str(adapter_dir)}
    message = json.dumps(payload, sort_keys=True).encode()
    signature = key.sign(message)
    manifest = {
        "payload": payload,
        "public_key": base64.b64encode(
            public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
        ).decode(),
        "signature": base64.b64encode(signature).decode(),
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    return path, manifest


def test_configure_adapter_success(tmp_path: Path) -> None:
    adapter_dir = _create_adapter(tmp_path)
    manifest_path, manifest = _create_manifest(tmp_path, adapter_dir)

    result = configure_adapter(
        "acme/sample@1.0.0", manifest_path, ["read"], "proj-success"
    )
    assert result == {"installation_status": "success", "health_check_result": True}
    installed = Path("adapters/proj-success/acme_sample@1.0.0")
    assert installed.exists()
    registry = yaml.safe_load(Path("configs/adapters.yaml").read_text())
    assert "acme/sample@1.0.0" in registry["proj-success"]


def test_configure_adapter_invalid_scope(tmp_path: Path) -> None:
    adapter_dir = _create_adapter(tmp_path)
    manifest_path, _ = _create_manifest(tmp_path, adapter_dir)

    with pytest.raises(ValueError):
        configure_adapter(
            "acme/sample@1.0.0", manifest_path, ["admin"], "proj-bad-scope"
        )


def test_configure_adapter_bad_signature(tmp_path: Path) -> None:
    adapter_dir = _create_adapter(tmp_path)
    manifest_path, manifest = _create_manifest(tmp_path, adapter_dir)
    bad = json.loads(manifest_path.read_text())
    bad["signature"] = base64.b64encode(b"0" * 64).decode()
    manifest_path.write_text(json.dumps(bad))

    with pytest.raises(ValueError):
        configure_adapter("acme/sample@1.0.0", manifest_path, ["read"], "proj-bad-sig")
