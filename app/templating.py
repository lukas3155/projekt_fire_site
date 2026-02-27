from datetime import datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from app.config import settings

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _csrf_input(request):
    """Return a hidden input with the CSRF token (set by CSRFMiddleware)."""
    token = getattr(request.state, "csrf_token", "") or request.cookies.get("csrf_token", "")
    return Markup(f'<input type="hidden" name="csrf_token" value="{token}">')


templates.env.globals.update({
    "site_url": settings.SITE_URL,
    "site_name": settings.SITE_NAME,
    "current_year": datetime.now().year,
    "csrf_input": _csrf_input,
})
