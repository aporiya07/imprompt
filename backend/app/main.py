import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import routes_analysis, routes_prompt
from app.config import get_settings
from app.models.contracts import ApiEnvelope, ErrorBody
from app.providers.registry import build_runtime
from app.services.observability import request_id_var
from app.utils.errors import AppError
from app.version import APP_VERSION

log = logging.getLogger("imprompt")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
    )
    runtime = build_runtime(settings)
    app.state.runtime = runtime
    log.info(
        "runtime ready: providers=%s vision=%s prompt=%s fallback=%s",
        sorted(runtime.providers) or "none",
        runtime.vision.cfg.primary,
        runtime.prompt.cfg.primary,
        settings.enable_fallback,
    )
    yield


app = FastAPI(title="ImPrompt", version=APP_VERSION, lifespan=lifespan)
app.include_router(routes_analysis.router)
app.include_router(routes_prompt.router)


def _error_response(status_code: int, code: str, message: str, request_id: str, details=None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ApiEnvelope(
            success=False,
            error=ErrorBody(code=code, message=message, details=details, request_id=request_id),
        ).model_dump(),
        headers={"x-request-id": request_id},
    )


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    rid = uuid.uuid4().hex[:12]
    request.state.request_id = rid
    request_id_var.set(rid)
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        log.exception("unhandled error [%s] %s %s", rid, request.method, request.url.path)
        return _error_response(500, "internal_error", "Unexpected server error.", rid)
    response.headers["x-request-id"] = rid
    log.info(
        "%s %s -> %s (%.2fs) [%s]",
        request.method, request.url.path, response.status_code, time.perf_counter() - started, rid,
    )
    return response


# CORS last = outermost so even middleware-caught 500s receive CORS headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    rid = getattr(request.state, "request_id", "-")
    log.warning("app error [%s] %s: %s", rid, exc.code, exc.message)
    return _error_response(exc.status_code, exc.code, exc.message, rid, exc.details or None)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    rid = getattr(request.state, "request_id", "-")
    errors = exc.errors()
    first = errors[0] if errors else {}
    loc = ".".join(str(part) for part in first.get("loc", [])[1:]) or "body"
    message = f"Invalid request field '{loc}': {first.get('msg', 'validation failed')}"
    details = [{"loc": [str(p) for p in e.get("loc", [])], "msg": e.get("msg", "")} for e in errors[:5]]
    return _error_response(400, "validation_error", message, rid, details)


# Serve the built frontend when it exists (single-process local deployment).
_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _DIST.exists():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="frontend")
