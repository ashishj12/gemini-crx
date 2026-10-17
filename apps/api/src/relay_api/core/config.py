"""Load only allowlisted configuration; never execute .env content or print secrets."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CHALLENGE_ROOT = ROOT / "resources/challenge"
KEYS = {
    "APP_MODE",
    "APP_HOST",
    "APP_PORT",
    "MOCK_HOST",
    "MOCK_PORT",
    "ENTERPRISE_API_BASE_URL",
    "DATABASE_PATH",
    "REQUEST_TIMEOUT",
    "MAX_RETRIES",
    "AI_TIMEOUT",
    "GEMINI_MODEL",
    "GEMINI_API_KEY",
    "COOKIE_SECURE",
    "PUBLIC_ORIGIN",
    "MOCK_ALLOW_FAILURES",
    "MOCK_AUTH_MODE",
    "MOCK_BILLING_MODE",
    "MOCK_LEGACY_MODE",
    "MOCK_CASE_MODE",
    "STRUCTURED_LOG_PATH",
    "GOOGLE_CLOUD_PROJECT",
}


def load_environment(path=None):
    file = Path(path) if path else ROOT / ".env"
    if file.exists():
        for raw in file.read_text(encoding="utf-8-sig").splitlines():
            raw = raw.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key not in KEYS:
                continue
            if len(value) > 1 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            if value:
                os.environ.setdefault(key, value)
    if os.name == "nt":
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as env:
                for key in ("GEMINI_API_KEY", "GEMINI_MODEL", "GOOGLE_CLOUD_PROJECT"):
                    if os.getenv(key):
                        continue
                    try:
                        value, _ = winreg.QueryValueEx(env, key)
                    except OSError:
                        continue
                    if isinstance(value, str) and value:
                        os.environ[key] = value
        except OSError:
            pass
