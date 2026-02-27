import secrets
from urllib.parse import parse_qs

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send


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


class CSRFMiddleware:
    """CSRF protection using double-submit cookie pattern (pure ASGI).

    Avoids BaseHTTPMiddleware which consumes the request body stream,
    making it unavailable to downstream route handlers.
    """

    COOKIE_NAME = "csrf_token"
    FIELD_NAME = "csrf_token"
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        # Ensure CSRF token exists
        csrf_cookie = request.cookies.get(self.COOKIE_NAME)
        if not csrf_cookie:
            csrf_cookie = secrets.token_hex(32)

        # Make token available to templates via request.state
        request.state.csrf_token = csrf_cookie

        # Validate on unsafe methods (POST, PUT, DELETE)
        if request.method not in self.SAFE_METHODS:
            path = request.url.path

            # Skip CSRF for API-like endpoints (HTMX sends its own headers)
            if not path.startswith("/htmx/"):
                content_type = request.headers.get("content-type", "")
                if "form" in content_type or "multipart" in content_type:
                    body = await request.body()

                    # Extract CSRF token from form data
                    if "multipart" not in content_type:
                        form_token = parse_qs(body.decode()).get(self.FIELD_NAME, [""])[0]
                    else:
                        form = await request.form()
                        form_token = str(form.get(self.FIELD_NAME, ""))
                        await form.close()

                    if not csrf_cookie or not secrets.compare_digest(str(form_token), csrf_cookie):
                        response = Response("CSRF validation failed", status_code=403)
                        await response(scope, receive, send)
                        return

                    # Replace receive so downstream handlers can re-read the body
                    async def cached_receive():
                        return {"type": "http.request", "body": body, "more_body": False}

                    receive = cached_receive

        # Inject CSRF cookie into response
        cookie = f"{self.COOKIE_NAME}={csrf_cookie}; Path=/; Max-Age=86400; SameSite=Strict"
        if request.url.scheme == "https":
            cookie += "; Secure"

        async def send_with_cookie(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"set-cookie", cookie.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_cookie)
