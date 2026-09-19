from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_FIXTURES = ROOT / "data" / "integrations"
FIXTURES = _DEFAULT_FIXTURES


def configure_fixtures(directory: Path | None = None) -> Path:
    """Point Stripe/Adyen mock fixtures at an alternate directory."""
    global FIXTURES
    FIXTURES = Path(directory) if directory is not None else _DEFAULT_FIXTURES
    return FIXTURES


def live_mode() -> bool:
    return os.environ.get("INTEGRATIONS_MODE", "mock").strip().lower() == "live"


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def load_json(path: Path):
    return json.loads(path.read_text())


def fixture_dir(provider: str) -> Path:
    return FIXTURES / provider


def constant_time_equal(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


def hmac_sha256_b64(raw: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).digest()
    import base64

    return base64.b64encode(digest).decode("ascii")


def hmac_sha256_hex_key_b64(raw: bytes, hex_key: str) -> str:
    import base64
    import binascii

    key = binascii.unhexlify(hex_key)
    digest = hmac.new(key, raw, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")
