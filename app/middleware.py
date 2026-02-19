import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    """Simple CSRF protection using double-submit cookie pattern."""

    COOKIE_NAME = "csrf_token"
    FIELD_NAME = "csrf_token"
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    async def dispatch(self, request: Request, call_next):
        # Ensure CSRF cookie exists
        csrf_cookie = request.cookies.get(self.COOKIE_NAME)
        if not csrf_cookie:
            csrf_cookie = secrets.token_hex(32)

        # Validate on unsafe methods (POST, PUT, DELETE)
        if request.method not in self.SAFE_METHODS:
            path = request.url.path

            # Skip CSRF for API-like endpoints (HTMX sends its own headers)
            if not path.startswith("/htmx/"):
                content_type = request.headers.get("content-type", "")
                if "form" in content_type or "multipart" in content_type:
                    form = await request.form()
                    form_token = form.get(self.FIELD_NAME, "")
                    if not csrf_cookie or not secrets.compare_digest(str(form_token), csrf_cookie):
                        return Response("CSRF validation failed", status_code=403)

        response: Response = await call_next(request)

        # Set/refresh CSRF cookie
        response.set_cookie(
            self.COOKIE_NAME,
            csrf_cookie,
            httponly=False,  # JS needs to read it for HTMX
            samesite="strict",
            secure=request.url.scheme == "https",
            max_age=3600 * 24,
        )

        return response
