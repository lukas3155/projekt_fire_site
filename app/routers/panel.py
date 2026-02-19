from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.article import Article, ArticleStatus
from app.models.category import Category
from app.models.comment import Comment
from app.services.article_service import (
    create_article,
    delete_article,
    get_all_categories,
    get_all_tags,
    get_article_by_id,
    get_articles,
    update_article,
)
from app.services.auth_service import authenticate_admin
from app.templating import templates
from app.utils.security import (
    check_rate_limit,
    create_access_token,
    decode_access_token,
    record_login_attempt,
)

router = APIRouter(prefix="/panel", tags=["panel"])

COOKIE_NAME = "session_token"


class RequireLoginException(Exception):
    pass


async def get_current_admin(request: Request) -> dict | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return decode_access_token(token)


async def require_admin(request: Request) -> dict:
    admin = await get_current_admin(request)
    if admin is None:
        raise RequireLoginException()
    return admin


# ──── Auth ────────────────────────────────────────────────────────────────────


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    admin = await get_current_admin(request)
    if admin:
        return RedirectResponse(url="/panel", status_code=303)
    return templates.TemplateResponse("panel/login.html", {"request": request})


@router.post("/login")
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")

    client_ip = request.client.host if request.client else "unknown"

    if not check_rate_limit(client_ip):
        return templates.TemplateResponse(
            "panel/login.html",
            {"request": request, "error": "Zbyt wiele prób logowania. Spróbuj za 15 minut."},
            status_code=429,
        )

    record_login_attempt(client_ip)

    admin = await authenticate_admin(db, username, password)
    if admin is None:
        return templates.TemplateResponse(
            "panel/login.html",
            {"request": request, "error": "Nieprawidłowa nazwa użytkownika lub hasło."},
            status_code=401,
        )

    token = create_access_token({"sub": admin.username, "admin_id": admin.id})
    response = RedirectResponse(url="/panel", status_code=303)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="strict",
        max_age=86400,
    )
    return response


@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/panel/login", status_code=303)
    response.delete_cookie(key=COOKIE_NAME)
    return response


# ──── Dashboard ───────────────────────────────────────────────────────────────


@router.get("", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count(Article.id)))).scalar() or 0
    published = (await db.execute(
        select(func.count(Article.id)).where(Article.status == ArticleStatus.PUBLISHED)
    )).scalar() or 0
    drafts = total - published
    comments = (await db.execute(select(func.count(Comment.id)))).scalar() or 0
    categories = (await db.execute(select(func.count(Category.id)))).scalar() or 0

    recent_articles, _ = await get_articles(db, page=1, per_page=5)

    return templates.TemplateResponse("panel/dashboard.html", {
        "request": request,
        "admin": admin,
        "active_page": "dashboard",
        "stats": {
            "articles": total,
            "published": published,
            "drafts": drafts,
            "comments": comments,
            "categories": categories,
        },
        "recent_articles": recent_articles,
    })


# ──── Articles CRUD ───────────────────────────────────────────────────────────


@router.get("/articles", response_class=HTMLResponse)
async def article_list(
    request: Request,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    articles, total = await get_articles(db)
    return templates.TemplateResponse("panel/articles/list.html", {
        "request": request,
        "admin": admin,
        "active_page": "articles",
        "articles": articles,
        "total": total,
    })


@router.get("/articles/new", response_class=HTMLResponse)
async def article_new(
    request: Request,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    categories = await get_all_categories(db)
    tags = await get_all_tags(db)
    return templates.TemplateResponse("panel/articles/form.html", {
        "request": request,
        "admin": admin,
        "active_page": "articles",
        "article": None,
        "categories": categories,
        "tags": tags,
    })


@router.post("/articles")
async def article_create(
    request: Request,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    tag_ids = [int(t) for t in form.getlist("tag_ids")]
    category_id = int(form.get("category_id")) if form.get("category_id") else None

    article = await create_article(
        db,
        title=form.get("title", ""),
        content_md=form.get("content_md", ""),
        excerpt=form.get("excerpt") or None,
        featured_image=form.get("featured_image") or None,
        category_id=category_id,
        tag_ids=tag_ids,
        status=ArticleStatus(form.get("status", "draft")),
        meta_title=form.get("meta_title") or None,
        meta_description=form.get("meta_description") or None,
    )
    return RedirectResponse(url=f"/panel/articles/{article.id}/edit?saved=1", status_code=303)


@router.get("/articles/{article_id}/edit", response_class=HTMLResponse)
async def article_edit(
    request: Request,
    article_id: int,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    article = await get_article_by_id(db, article_id)
    if not article:
        return RedirectResponse(url="/panel/articles", status_code=303)

    categories = await get_all_categories(db)
    tags = await get_all_tags(db)

    return templates.TemplateResponse("panel/articles/form.html", {
        "request": request,
        "admin": admin,
        "active_page": "articles",
        "article": article,
        "categories": categories,
        "tags": tags,
        "flash_success": "Artykuł zapisany." if request.query_params.get("saved") else None,
    })


@router.post("/articles/{article_id}")
async def article_update(
    request: Request,
    article_id: int,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    article = await get_article_by_id(db, article_id)
    if not article:
        return RedirectResponse(url="/panel/articles", status_code=303)

    form = await request.form()
    tag_ids = [int(t) for t in form.getlist("tag_ids")]
    category_id = int(form.get("category_id")) if form.get("category_id") else None

    await update_article(
        db,
        article,
        title=form.get("title", ""),
        content_md=form.get("content_md", ""),
        excerpt=form.get("excerpt") or None,
        featured_image=form.get("featured_image") or None,
        category_id=category_id,
        tag_ids=tag_ids,
        status=ArticleStatus(form.get("status", "draft")),
        meta_title=form.get("meta_title") or None,
        meta_description=form.get("meta_description") or None,
    )
    return RedirectResponse(url=f"/panel/articles/{article_id}/edit?saved=1", status_code=303)


@router.post("/articles/{article_id}/delete")
async def article_delete(
    request: Request,
    article_id: int,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    article = await get_article_by_id(db, article_id)
    if article:
        await delete_article(db, article)
    return RedirectResponse(url="/panel/articles", status_code=303)
