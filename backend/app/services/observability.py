"""Stage-level observability (spec Phase 18).

Every pipeline execution logs one line per stage:
    stage=<name> status=ok|failed latency_ms=<n> request_id=<id>
Failures name the exact stage that broke. No image contents, no keys, ever.
"""
import logging
import time
from contextlib import asynccontextmanager
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

logger = logging.getLogger("ipa.pipeline")


@asynccontextmanager
async def stage(name: str):
    started = time.perf_counter()
    try:
        yield
    except Exception as e:
        logger.warning(
            "stage=%s status=failed latency_ms=%.0f request_id=%s error=%s",
            name,
            (time.perf_counter() - started) * 1000,
            request_id_var.get(),
            getattr(e, "code", type(e).__name__),
        )
        raise
    else:
        logger.info(
            "stage=%s status=ok latency_ms=%.0f request_id=%s",
            name,
            (time.perf_counter() - started) * 1000,
            request_id_var.get(),
        )
