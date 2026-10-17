"""Start the complete local workspace; Ctrl+C stops only owned child processes."""

import os
import subprocess
import shutil
import sys
import time
from pathlib import Path
from processes import stop_children

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api/src"))
from relay_api.core.config import load_environment  # noqa: E402

load_environment()
os.chdir(ROOT)
env = dict(os.environ)
env.setdefault("APP_MODE", "REVIEWER")
env.setdefault("MOCK_ALLOW_FAILURES", "true" if env["APP_MODE"] == "REVIEWER" else "false")
children = []
try:
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT / "apps/api/src"), str(ROOT / "services/mock-telecom/src")])
    api_env = dict(env, PORT=env.get("APP_PORT", "8080"))
    for module in ("relay_mock", "relay_api"):
        children.append(subprocess.Popen([sys.executable, "-m", module], env=api_env))
    bun = shutil.which("bun")
    if not bun:
        raise RuntimeError("Bun is required; run bun install first")
    env["RELAY_API_URL"] = "http://127.0.0.1:" + env.get("APP_PORT", "8080")
    web_env = {k: v for k, v in env.items() if k not in {"GEMINI_API_KEY", "GEMINI_MODEL"}}
    children.append(subprocess.Popen([bun, "--no-env-file", "run", "dev"], cwd=ROOT, env=web_env))
    print("Open http://127.0.0.1:" + web_env.get("PORT", "3000"), flush=True)
    while all(c.poll() is None for c in children):
        time.sleep(0.5)
finally:
    stop_children(children)
