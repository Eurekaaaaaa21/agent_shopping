import uuid
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        elapsed = time.time() - start_time
        logger.info(f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({elapsed:.3f}s)")
        return response
