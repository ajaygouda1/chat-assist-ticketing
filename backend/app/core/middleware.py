import uuid
import time
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.redis import redis_manager
from app.core.logger import logger

class TraceAndSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:10]}"
        request.state.request_id = req_id

        # Rate Limiting for Auth & Sensitive endpoints
        path = request.url.path
        client_ip = request.client.host if request.client else "127.0.0.1"

        if path.startswith("/api/v1/auth/login") or path.startswith("/api/v1/auth/register"):
            allowed = redis_manager.check_rate_limit(f"auth:{client_ip}", limit=15, window_sec=600)
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "success": False,
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many login/registration attempts. Please try again in 10 minutes.",
                            "request_id": req_id
                        }
                    }
                )

        start_time = time.time()
        response: Response = await call_next(request)
        process_time = round((time.time() - start_time) * 1000, 2)

        # Attach Trace Headers & Security Headers
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Process-Time-Ms"] = str(process_time)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response

async def custom_http_exception_handler(request: Request, exc: HTTPException):
    req_id = getattr(request.state, "request_id", "req_system")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "request_id": req_id
            }
        }
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "req_system")
    logger.error(f"Unhandled error: {str(exc)}", extra={"request_id": req_id})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected system error occurred. Please contact support.",
                "request_id": req_id
            }
        }
    )
