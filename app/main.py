import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import async_session, engine
from app.middleware import CSRFMiddleware, SecurityHeadersMiddleware

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent


async def _ensure_admin():
    """Create or update admin user from env vars on startup."""
    from sqlalchemy import select
    from app.database import async_session
    from app.models.admin import AdminUser
    from app.utils.security import hash_password

    async with async_session() as session:
        result = await session.execute(
            select(AdminUser).where(AdminUser.username == settings.ADMIN_USERNAME)
        )
        admin = result.scalar_one_or_none()

        if admin is None:
            session.add(AdminUser(
                username=settings.ADMIN_USERNAME,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
            ))
        else:
            admin.password_hash = hash_password(settings.ADMIN_PASSWORD)

        await session.commit()


async def _scheduled_publish_loop():
    """Background task: publish scheduled articles every 60 seconds."""
    from app.services.article_service import publish_scheduled_articles

    while True:
        await asyncio.sleep(60)
        try:
            async with async_session() as session:
                count = await publish_scheduled_articles(session)
                if count:
                    logger.info("Published %d scheduled article(s)", count)
        except Exception:
            logger.exception("Scheduled publish error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _ensure_admin()
    task = asyncio.create_task(_scheduled_publish_loop())
    yield
    task.cancel()
    await engine.dispose()


app = FastAPI(
    title=settings.SITE_NAME,
    docs_url="/docs" if settings.ENV == "development" else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Routers - order matters: specific routes before catch-all /{slug}
from app.routers.panel import RequireLoginException, router as panel_router  # noqa: E402
from app.routers.pages import router as pages_router  # noqa: E402
from app.routers.htmx import router as htmx_router  # noqa: E402
from app.routers.seo import router as seo_router  # noqa: E402
from app.routers.blog import router as blog_router  # noqa: E402

app.include_router(panel_router)
app.include_router(pages_router)
app.include_router(htmx_router)
app.include_router(seo_router)
app.include_router(blog_router)  # Must be last - contains catch-all /{slug}


@app.exception_handler(RequireLoginException)
async def require_login_handler(request: Request, exc: RequireLoginException):
    return RedirectResponse(url="/panel/login", status_code=303)
