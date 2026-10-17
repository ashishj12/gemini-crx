import importlib.util
import socket
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
import pytest
import uvicorn
from relay_api.application.workflows import ResolutionService
from relay_api.http.app import create_app

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def stack(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "REVIEWER")
    monkeypatch.setenv("MOCK_ALLOW_FAILURES", "true")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "app.sqlite"))
    monkeypatch.setenv("STRUCTURED_LOG_PATH", str(tmp_path / "events.jsonl"))
    monkeypatch.delenv("PUBLIC_ORIGIN", raising=False)
    for name in ("AUTH", "BILLING", "LEGACY", "CASE"):
        monkeypatch.delenv("MOCK_" + name + "_MODE", raising=False)
    spec = importlib.util.spec_from_file_location(
        "mock_server", ROOT / "services/mock-telecom/src/relay_mock/server.py"
    )
    mock = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mock)
    enterprise = ThreadingHTTPServer(("127.0.0.1", 0), mock.H)
    threading.Thread(target=enterprise.serve_forever, daemon=True).start()
    service = ResolutionService(str(tmp_path / "app.sqlite"), f"http://127.0.0.1:{enterprise.server_port}")
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(create_app(service), log_level="error", access_log=False))
    thread = threading.Thread(target=lambda: server.run(sockets=[sock]), daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("test_api_startup_failed")
        time.sleep(0.01)
    yield service, mock, f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)
    enterprise.shutdown()
    enterprise.server_close()
    service.store.db.close()


@pytest.fixture
def customer(stack):
    return stack[0].login({"username": "alex.morgan", "password": "ReviewerPass-1001"})[1]
