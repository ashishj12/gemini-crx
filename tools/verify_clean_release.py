"""Extract the source archive into an isolated folder and verify the documented setup."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE_PYTHON = sys.executable


def verify():
    output = ROOT / "evidence/current/clean-verification.json"
    work = ROOT / ".local" / ("clean-" + str(int(time.time())))
    work.mkdir(parents=True)
    with zipfile.ZipFile(ROOT / "release/relay-cx-production-source.zip") as archive:
        archive.extractall(work)
    source = work / "relay-cx"
    env = dict(os.environ)
    for key in ("GEMINI_API_KEY", "GEMINI_MODEL", "PYTHONPATH", "PUBLIC_ORIGIN", "DATABASE_PATH"):
        env.pop(key, None)
    env["APP_MODE"] = "REVIEWER"
    env["NEXT_TELEMETRY_DISABLED"] = "1"
    commands = []

    def run(args):
        result = subprocess.run(
            args, cwd=source, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        commands.append(
            {
                "command": " ".join(str(x) for x in args),
                "exitCode": result.returncode,
                "output": result.stdout[-8000:],
            }
        )
        print(Path(str(args[0])).name, "PASS" if result.returncode == 0 else "FAIL", flush=True)
        if result.returncode:
            raise RuntimeError("clean_command_failed")

    try:
        run([BASE_PYTHON, "-m", "venv", str(source / ".venv")])
        python = source / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run([str(python), "-m", "pip", "install", "-r", "requirements-dev.txt"])
        run([shutil.which("bun"), "install", "--frozen-lockfile"])
        run([str(python), "-m", "pytest", "-q"])
        run([str(python), "tools/evaluate.py", "--mode", "REVIEWER"])
        for script in ("test:web", "typecheck", "build"):
            run([shutil.which("bun"), "run", script])
        status = "PASS"
    except Exception:
        status = "FAIL"
    output.write_text(
        json.dumps(
            {
                "status": status,
                "isolatedSource": str(source),
                "credentialsPresent": False,
                "commands": commands,
            },
            indent=2,
        )
    )
    return status


if __name__ == "__main__":
    sys.exit(0 if verify() == "PASS" else 1)
