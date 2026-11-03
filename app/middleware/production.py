from collections import defaultdict, deque
from time import monotonic
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.config import settings

logger = logging.getLogger("pulse.errors")

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.hits = defaultdict(deque)

    async def dispatch(self, request, call_next):
        now = monotonic()
        login = request.url.path == "/api/v1/auth/token"
        key = (request.client.host if request.client else "unknown", login)
        limit = settings.login_rate_limit_per_minute if login else settings.rate_limit_per_minute
        for old_key in list(self.hits):
            if not self.hits[old_key] or self.hits[old_key][-1] <= now - 60:
                del self.hits[old_key]
        hits = self.hits[key]
        while hits and hits[0] <= now - 60:
            hits.popleft()
        if len(hits) >= limit:
            return JSONResponse({"detail": "Superé el límite de peticiones", "status_code": 429}, status_code=429, headers={"Retry-After": str(max(1, int(60 - (now - hits[0]))))})
        hits.append(now)
        return await call_next(request)

class ErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception:
            logger.exception("request_id=%s error interno", getattr(request.state, "request_id", "unknown"))
            return JSONResponse({"detail": "Ocurrió un error interno", "error_code": "INTERNAL_ERROR", "status_code": 500}, status_code=500)
