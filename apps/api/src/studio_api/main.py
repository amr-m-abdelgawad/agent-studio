from __future__ import annotations

import os
from contextlib import asynccontextmanager

import httpx
import psycopg
from fastapi import FastAPI, Response, status
from fastapi.exceptions import RequestValidationError
from studio_object_store.minio_store import MinioObjectStore
from studio_vault.vault_store import VaultSecretStore

from studio_api.db import get_session_factory, init_db
from studio_api.errors import APIError, api_error_handler, validation_exception_handler
from studio_api.middleware.request import RequestMiddleware
from studio_api.routers import api_keys, audit, auth, debug, me, org, workspaces
from studio_api.services.invites import bootstrap_org


def _maybe_setup_otel(app: FastAPI) -> None:
    if os.environ.get("OTEL_ENABLED", "false").lower() != "true":
        return
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({"service.name": "agent-studio-api"})
    provider = TracerProvider(resource=resource)
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _maybe_setup_otel(app)
    init_db()
    db = get_session_factory()()
    try:
        bootstrap_org(db)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    yield


app = FastAPI(title="Agent Studio API", lifespan=lifespan)

app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.add_middleware(RequestMiddleware)

app.include_router(auth.router)
app.include_router(me.router)
app.include_router(org.router)
app.include_router(workspaces.router)
app.include_router(api_keys.router)
app.include_router(audit.router)
app.include_router(debug.router)


def _postgres_ok() -> bool:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return False
    try:
        with psycopg.connect(database_url, connect_timeout=3) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


def _temporal_ok() -> bool:
    host = os.environ.get("TEMPORAL_HOST", "temporal:7233")
    try:
        with httpx.Client(timeout=3.0) as client:
            response = client.get(f"http://{host.replace(':7233', ':8233')}/")
            return response.status_code < 500
    except Exception:
        try:
            import socket

            hostname, _, port_str = host.partition(":")
            port = int(port_str or "7233")
            with socket.create_connection((hostname, port), timeout=3):
                return True
        except Exception:
            return False


def _minio_ok() -> bool:
    return MinioObjectStore().ping()


def _vault_ok() -> bool:
    return VaultSecretStore().ping()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready(response: Response) -> dict[str, object]:
    checks = {
        "postgres": _postgres_ok(),
        "temporal": _temporal_ok(),
        "minio": _minio_ok(),
        "vault": _vault_ok(),
    }
    all_ok = all(checks.values())
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ready" if all_ok else "not_ready", "checks": checks}
