from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.SITE_NAME,
    docs_url="/docs" if settings.ENV == "development" else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Routers — order matters: specific routes before catch-all /{slug}
from app.routers.panel import RequireLoginException, router as panel_router  # noqa: E402
from app.routers.pages import router as pages_router  # noqa: E402
from app.routers.htmx import router as htmx_router  # noqa: E402
from app.routers.blog import router as blog_router  # noqa: E402

app.include_router(panel_router)
app.include_router(pages_router)
app.include_router(htmx_router)
app.include_router(blog_router)  # Must be last — contains catch-all /{slug}


@app.exception_handler(RequireLoginException)
async def require_login_handler(request: Request, exc: RequireLoginException):
    return RedirectResponse(url="/panel/login", status_code=303)
