"""ASGI transport. Business workflows and deterministic security live in the service layer."""

from contextlib import asynccontextmanager
import os
import time
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from relay_api.application.workflows import ResolutionService
from relay_api.core.config import CHALLENGE_ROOT, load_environment
from relay_api.domain.models import Chat, Confirmation, Login
from relay_api.evaluation.scenarios import run_scenario
from relay_api.infrastructure.enterprise import Denied, IntegrationError


def create_app(engine: ResolutionService | None = None) -> FastAPI:
    load_environment()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = engine or ResolutionService()
        yield
        if engine is None:
            app.state.engine.store.db.close()

    app = FastAPI(
        title="Relay Resolution API",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs" if os.getenv("APP_MODE", "REVIEWER") == "REVIEWER" else None,
    )
    app.state.attempts = defaultdict(list)
    if engine is not None:
        app.state.engine = engine

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        if request.method == "POST":
            try:
                if int(request.headers.get("content-length", "0")) > 8192:
                    return JSONResponse({"error": "invalid_body_size"}, 413)
            except ValueError:
                return JSONResponse({"error": "invalid_request"}, 400)
            if request.headers.get("content-type", "").split(";")[0] != "application/json":
                return JSONResponse({"error": "json_required"}, 415)
            origin = request.headers.get("origin")
            expected = os.getenv("PUBLIC_ORIGIN", str(request.base_url).rstrip("/"))
            if origin and origin != expected:
                return JSONResponse({"error": "origin_denied"}, 403)
        response = await call_next(request)
        response.headers.update(
            {
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
            }
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, error):
        return JSONResponse({"error": "invalid_request"}, 400)

    @app.exception_handler(Denied)
    async def denied(request, error):
        return JSONResponse({"error": "access_denied"}, 403)

    @app.exception_handler(IntegrationError)
    async def integration_error(request, error):
        status = 401 if error.reason in ("http_401", "expired_identity") else 503
        return JSONResponse(
            {
                "error": "authentication_failed"
                if error.service == "authentication"
                else "enterprise_unavailable"
            },
            status,
        )

    def session(request: Request, support=False):
        service = request.app.state.engine
        current = service.store.session(request.cookies.get("cx_session", ""))
        if current is None:
            from fastapi import HTTPException

            raise HTTPException(401, "authentication_required")
        if support and "support-agent" not in current["roles"]:
            raise Denied("support_role_required")
        return current

    def set_cookie(response, token, age=3600):
        response.set_cookie(
            "cx_session",
            token,
            max_age=age,
            httponly=True,
            samesite="strict",
            secure=os.getenv("COOKIE_SECURE") == "true",
            path="/",
        )

    @app.get("/health")
    def health(request: Request):
        return {"status": "ok", "mode": request.app.state.engine.mode}

    @app.post("/api/login")
    def login(request: Request, data: Login):
        service = request.app.state.engine
        now = time.time()
        ip = request.client.host if request.client else "unknown"
        with service.store.lock:
            times = [t for t in app.state.attempts[ip] if now - t < 60]
            if len(times) >= 30:
                return JSONResponse({"error": "login_rate_limited"}, 429)
            app.state.attempts[ip] = times + [now]
        token, current = service.login(data.model_dump())
        response = JSONResponse({"customerId": current["customerId"], "mode": current["mode"]})
        set_cookie(response, token)
        return response

    @app.get("/api/session")
    def get_session(request: Request):
        current = session(request)
        return {
            k: current.get(k) for k in ("customerId", "accountId", "roles", "mode", "state", "history")
        } | {"pendingAction": current.get("pending")}

    @app.post("/api/logout")
    def logout(request: Request):
        current = session(request)
        current["expires"] = 0
        request.app.state.engine.store.save(current)
        response = JSONResponse({"status": "signed_out"})
        set_cookie(response, "", 0)
        return response

    @app.post("/api/chat")
    @app.post("/chat", include_in_schema=False)
    def chat(request: Request, data: Chat):
        service = request.app.state.engine
        with service.store.lock:
            return service.chat(session(request), data)

    @app.post("/api/confirm")
    def confirm(request: Request, data: Confirmation):
        service = request.app.state.engine
        with service.store.lock:
            return service.confirm(session(request), data)

    @app.get("/api/account/overview")
    def overview(request: Request):
        return request.app.state.engine.overview(session(request))

    @app.get("/api/scenarios")
    def scenarios(request: Request):
        import json

        session(request)
        return [json.loads(p.read_text()) for p in sorted((CHALLENGE_ROOT / "scenarios").glob("*.json"))]

    @app.post("/api/reviewer/run")
    def reviewer(request: Request, data: dict):
        service = request.app.state.engine
        session(request, support=True)
        if service.mode != "REVIEWER":
            raise Denied("reviewer_mode_required")
        try:
            with service.store.lock:
                return run_scenario(service, data.get("scenarioId", ""))
        except ValueError:
            return JSONResponse({"error": "invalid_request"}, 400)

    @app.get("/api/traces/{trace_id}")
    def trace(request: Request, trace_id: str):
        current = session(request)
        events = [
            e
            for e in request.app.state.engine.store.events()
            if e["traceId"] == trace_id
            and (e["sessionId"] == current["id"] or "support-agent" in current["roles"])
        ]
        return events if events else JSONResponse({"error": "not_found"}, 404)

    @app.get("/api/ops/{view}")
    def operations(request: Request, view: str):
        current = session(request, support=True)
        service = request.app.state.engine
        if view == "metrics":
            return service.store.metrics()
        if view == "events":
            return service.store.events()
        if view == "escalations":
            return [r for _, r in service.store.escalations()]
        if view == "health":
            from relay_api.infrastructure.storage import uid

            try:
                return {
                    "enterprise": service.gateway.request("health", "/health", uid("TRACE"), current),
                    "aiMode": service.mode,
                }
            except IntegrationError:
                return {"enterprise": {"status": "unavailable"}, "aiMode": service.mode}
        return JSONResponse({"error": "not_found"}, 404)

    return app
