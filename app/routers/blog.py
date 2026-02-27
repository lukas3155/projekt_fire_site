import math

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.article import Article, ArticleStatus
from app.models.category import Category
from app.services.article_service import get_all_categories, get_articles
from app.config import settings
from app.templating import templates

router = APIRouter(tags=["blog"])

PER_PAGE = 10
_BASE = settings.SITE_URL


async def _sidebar_data(db: AsyncSession) -> dict:
    return {
        "sidebar_categories": await get_all_categories(db),
    }


# ──── Blog list ───────────────────────────────────────────────────────────────


@router.get("/", response_class=HTMLResponse)
async def homepage(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await _render_blog_list(request, db, page=1)


@router.get("/blog", response_class=HTMLResponse)
async def blog_redirect():
    return RedirectResponse(url="/", status_code=301)


@router.get("/page/{page_num}", response_class=HTMLResponse)
async def blog_list_paginated(
    request: Request,
    page_num: int,
    db: AsyncSession = Depends(get_db),
):
    if page_num <= 1:
        return RedirectResponse(url="/", status_code=301)
    return await _render_blog_list(request, db, page=page_num)


@router.get("/blog/page/{page_num}", response_class=HTMLResponse)
async def blog_page_redirect(page_num: int):
    if page_num <= 1:
        return RedirectResponse(url="/", status_code=301)
    return RedirectResponse(url=f"/page/{page_num}", status_code=301)


async def _render_blog_list(request: Request, db: AsyncSession, page: int):
    articles, total = await get_articles(db, status=ArticleStatus.PUBLISHED, page=page, per_page=PER_PAGE)
    total_pages = math.ceil(total / PER_PAGE) if total > 0 else 1
    sidebar = await _sidebar_data(db)

    return templates.TemplateResponse("blog/list.html", {
        "request": request,
        "active_nav": "blog",
        "articles": articles,
        "current_page": page,
        "total_pages": total_pages,
        "base_url": "",
        "breadcrumbs_jsonld": [
            {"name": "Strona główna", "url": _BASE},
        ],
        **sidebar,
    })


# ──── Category ────────────────────────────────────────────────────────────────


@router.get("/kategoria/{slug}", response_class=HTMLResponse)
async def category_page(
    request: Request,
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    return await _render_category(request, db, slug, page=1)


@router.get("/kategoria/{slug}/page/{page_num}", response_class=HTMLResponse)
async def category_page_paginated(
    request: Request,
    slug: str,
    page_num: int,
    db: AsyncSession = Depends(get_db),
):
    if page_num <= 1:
        return RedirectResponse(url=f"/kategoria/{slug}", status_code=301)
    return await _render_category(request, db, slug, page=page_num)


async def _render_category(request: Request, db: AsyncSession, slug: str, page: int):
    result = await db.execute(select(Category).where(Category.slug == slug))
    category = result.scalar_one_or_none()
    if not category:
        return templates.TemplateResponse("pages/404.html", {"request": request}, status_code=404)

    count_q = select(func.count(Article.id)).where(
        Article.status == ArticleStatus.PUBLISHED,
        Article.category_id == category.id,
    )
    total = (await db.execute(count_q)).scalar() or 0

    articles_q = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.tags))
        .where(Article.status == ArticleStatus.PUBLISHED, Article.category_id == category.id)
        .order_by(Article.published_at.desc())
        .offset((page - 1) * PER_PAGE)
        .limit(PER_PAGE)
    )
    articles = list((await db.execute(articles_q)).scalars().all())
    total_pages = math.ceil(total / PER_PAGE) if total > 0 else 1

    return templates.TemplateResponse("blog/category.html", {
        "request": request,
        "active_nav": "blog",
        "category": category,
        "articles": articles,
        "current_page": page,
        "total_pages": total_pages,
        "base_url": f"/kategoria/{slug}",
        "breadcrumbs_jsonld": [
            {"name": "Strona główna", "url": _BASE},
            {"name": "Blog", "url": f"{_BASE}/blog"},
            {"name": category.name, "url": f"{_BASE}/kategoria/{slug}"},
        ],
    })


# ──── Article detail (catch-all, must be LAST) ───────────────────────────────


@router.get("/{slug}", response_class=HTMLResponse)
async def article_detail(
    request: Request,
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.tags))
        .where(Article.slug == slug, Article.status == ArticleStatus.PUBLISHED)
    )
    article = result.scalar_one_or_none()
    if not article:
        return templates.TemplateResponse("pages/404.html", {"request": request}, status_code=404)

    breadcrumbs = [
        {"name": "Strona główna", "url": _BASE},
        {"name": "Blog", "url": f"{_BASE}/blog"},
    ]
    if article.category:
        breadcrumbs.append({"name": article.category.name, "url": f"{_BASE}/kategoria/{article.category.slug}"})
    breadcrumbs.append({"name": article.title, "url": f"{_BASE}/{article.slug}"})

    return templates.TemplateResponse("blog/detail.html", {
        "request": request,
        "active_nav": "blog",
        "article": article,
        "article_jsonld": article,
        "breadcrumbs_jsonld": breadcrumbs,
    })
