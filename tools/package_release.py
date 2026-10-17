"""Create a source-only release with an allowlist, secret scan and content manifest."""

import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api/src"))
from relay_api.core.config import load_environment  # noqa: E402

DIRECTORIES = (
    "apps",
    "services",
    "resources",
    "tests",
    "tools",
    "docs",
    "deployment",
    "evidence/current",
    ".github",
)
FILES = (
    "README.md",
    "package.json",
    "bun.lock",
    "pyproject.toml",
    "requirements-dev.txt",
    "compose.yaml",
    ".dockerignore",
    ".gitignore",
    ".env.example",
)
EXCLUDED = {"node_modules", ".next", "__pycache__", ".pytest_cache", ".ruff_cache", ".local"}


def source_files():
    files = [ROOT / f for f in FILES]
    for directory in DIRECTORIES:
        for current, directories, names in os.walk(ROOT / directory, followlinks=False):
            directories[:] = [d for d in directories if d not in EXCLUDED and not d.endswith(".egg-info")]
            files.extend(Path(current) / name for name in names)
    return sorted(
        {
            p
            for p in files
            if not any(part in EXCLUDED or part.endswith(".egg-info") for part in p.relative_to(ROOT).parts)
            and p.suffix not in {".pyc", ".mp4", ".zip", ".tsbuildinfo"}
            and p.name not in {".env", "pnpm-lock.yaml"}
        },
        key=lambda p: p.relative_to(ROOT).as_posix(),
    )


def package():
    load_environment()
    secret = os.getenv("GEMINI_API_KEY", "").encode()
    members = {}
    manifest = {}
    for p in source_files():
        name = p.relative_to(ROOT).as_posix()
        body = p.read_bytes()
        if p.is_symlink() or (secret and secret in body):
            raise ValueError("Release rejected: symlink or configured secret in " + name)
        if p.suffix in {".sqlite", ".db", ".exe", ".dll", ".pem", ".key"}:
            raise ValueError("Unexpected runtime/secret file: " + name)
        members[name] = body
        manifest[name] = hashlib.sha256(body).hexdigest()
    release = ROOT / "release"
    release.mkdir(exist_ok=True)
    output = release / "relay-cx-production-source.zip"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, body in members.items():
            z.writestr("relay-cx/" + name, body)
        z.writestr("relay-cx/SOURCE_MANIFEST.json", json.dumps(manifest, indent=2))
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    (release / "SHA256SUMS.txt").write_text(checksum + "  " + output.name + "\n")
    print(
        json.dumps(
            {
                "archive": str(output),
                "files": len(members),
                "bytes": output.stat().st_size,
                "sha256": checksum,
                "secretScan": "PASS",
                "demoVideo": "EXCLUDED",
            }
        )
    )
    return output


if __name__ == "__main__":
    package()
