from datetime import datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.config import settings

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=BASE_DIR / "templates")

templates.env.globals.update({
    "site_url": settings.SITE_URL,
    "site_name": settings.SITE_NAME,
    "current_year": datetime.now().year,
})
