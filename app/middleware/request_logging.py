import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("pulse.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        started = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{elapsed:.2f}"
        logger.info("%s %s %s %.2fms", request.method, request.url.path, response.status_code, elapsed)
        return response
