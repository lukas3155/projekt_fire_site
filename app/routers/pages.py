import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.article import Article, ArticleStatus, article_tag
from app.models.contact_message import ContactMessage
from app.models.static_page import StaticPage
from app.models.tag import Tag
from app.templating import templates

logger = logging.getLogger(__name__)

router = APIRouter(tags=["pages"])


@router.get("/tutaj-zacznij", response_class=HTMLResponse)
async def start_here(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Get articles with "beginner" tag
    result = await db.execute(select(Tag).where(Tag.slug == "beginner"))
    beginner_tag = result.scalar_one_or_none()

    articles = []
    if beginner_tag:
        articles_q = (
            select(Article)
            .options(selectinload(Article.category), selectinload(Article.tags))
            .join(article_tag, Article.id == article_tag.c.article_id)
            .where(
                Article.status == ArticleStatus.PUBLISHED,
                article_tag.c.tag_id == beginner_tag.id,
            )
            .order_by(Article.published_at.desc())
        )
        articles = list((await db.execute(articles_q)).scalars().all())

    return templates.TemplateResponse("pages/start_here.html", {
        "request": request,
        "active_nav": "start",
        "articles": articles,
        "breadcrumbs_jsonld": [
            {"name": "Strona główna", "url": settings.SITE_URL},
            {"name": "Tutaj zacznij", "url": f"{settings.SITE_URL}/tutaj-zacznij"},
        ],
    })


@router.get("/o-mnie", response_class=HTMLResponse)
async def about(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StaticPage).where(StaticPage.slug == "o-mnie"))
    page = result.scalar_one_or_none()

    if not page:
        return templates.TemplateResponse("pages/404.html", {"request": request}, status_code=404)

    return templates.TemplateResponse("pages/about.html", {
        "request": request,
        "active_nav": "about",
        "page": page,
        "breadcrumbs_jsonld": [
            {"name": "Strona główna", "url": settings.SITE_URL},
            {"name": "O mnie", "url": f"{settings.SITE_URL}/o-mnie"},
        ],
    })


@router.get("/kontakt", response_class=HTMLResponse)
async def contact_page(request: Request):
    return templates.TemplateResponse("pages/contact.html", {
        "request": request,
        "active_nav": "contact",
        "contact_email": settings.CONTACT_EMAIL,
        "breadcrumbs_jsonld": [
            {"name": "Strona główna", "url": settings.SITE_URL},
            {"name": "Kontakt", "url": f"{settings.SITE_URL}/kontakt"},
        ],
    })


@router.get("/kalkulator-fire", response_class=HTMLResponse)
async def calculator_fire(request: Request):
    return templates.TemplateResponse("pages/calculator_fire.html", {
        "request": request,
        "active_nav": "calculator",
        "breadcrumbs_jsonld": [
            {"name": "Strona główna", "url": settings.SITE_URL},
            {"name": "Kalkulator FIRE", "url": f"{settings.SITE_URL}/kalkulator-fire"},
        ],
    })


@router.get("/kalkulator-procent-skladany", response_class=HTMLResponse)
async def calculator_compound(request: Request):
    return templates.TemplateResponse("pages/calculator_compound.html", {
        "request": request,
        "active_nav": "calculator",
        "breadcrumbs_jsonld": [
            {"name": "Strona główna", "url": settings.SITE_URL},
            {"name": "Kalkulator procentu składanego", "url": f"{settings.SITE_URL}/kalkulator-procent-skladany"},
        ],
    })


@router.post("/kontakt", response_class=HTMLResponse)
async def contact_submit(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()

    # Honeypot check
    if form.get("website"):
        return templates.TemplateResponse("pages/contact.html", {
            "request": request,
            "active_nav": "contact",
            "contact_email": settings.CONTACT_EMAIL,
            "success": True,  # Pretend success for bots
        })

    name = form.get("name", "").strip()
    email = form.get("email", "").strip()
    subject = form.get("subject", "").strip()
    message = form.get("message", "").strip()

    if not all([name, email, subject, message]):
        return templates.TemplateResponse("pages/contact.html", {
            "request": request,
            "active_nav": "contact",
            "contact_email": settings.CONTACT_EMAIL,
            "error": "Wszystkie pola są wymagane.",
        })

    client_ip = request.client.host if request.client else None
    db.add(ContactMessage(
        name=name, email=email, subject=subject, message=message, ip_address=client_ip,
    ))
    await db.commit()
    logger.info("Contact form saved: name=%s, email=%s, subject=%s", name, email, subject)

    return templates.TemplateResponse("pages/contact.html", {
        "request": request,
        "active_nav": "contact",
        "contact_email": settings.CONTACT_EMAIL,
        "success": True,
    })
