from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.article import Article, ArticleStatus
from app.models.blacklisted_word import BlacklistedWord
from app.models.category import Category
from app.models.comment import Comment
from app.models.static_page import StaticPage
from app.models.tag import Tag
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
from app.services.media_service import delete_media, get_all_media, upload_media
from app.templating import templates
from app.utils.markdown import render_markdown
from app.utils.seo import generate_slug
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


# ──── Categories CRUD ─────────────────────────────────────────────────────────


@router.get("/categories", response_class=HTMLResponse)
async def categories_page(
    request: Request,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Category).options(selectinload(Category.articles)).order_by(Category.name)
    )
    categories = list(result.scalars().all())

    editing = None
    edit_id = request.query_params.get("edit")
    if edit_id:
        editing = next((c for c in categories if c.id == int(edit_id)), None)

    return templates.TemplateResponse("panel/categories.html", {
        "request": request,
        "admin": admin,
        "active_page": "categories",
        "categories": categories,
        "editing": editing,
        "flash_success": request.query_params.get("saved") and "Zapisano." or None,
    })


@router.post("/categories")
async def category_create(
    request: Request,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    name = form.get("name", "").strip()
    description = form.get("description", "").strip() or None
    slug = generate_slug(name)

    category = Category(name=name, slug=slug, description=description)
    db.add(category)
    await db.commit()
    return RedirectResponse(url="/panel/categories?saved=1", status_code=303)


@router.post("/categories/{category_id}")
async def category_update(
    request: Request,
    category_id: int,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        return RedirectResponse(url="/panel/categories", status_code=303)

    form = await request.form()
    category.name = form.get("name", "").strip()
    category.description = form.get("description", "").strip() or None
    category.slug = generate_slug(category.name)
    await db.commit()
    return RedirectResponse(url="/panel/categories?saved=1", status_code=303)


@router.post("/categories/{category_id}/delete")
async def category_delete(
    request: Request,
    category_id: int,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if category:
        await db.delete(category)
        await db.commit()
    return RedirectResponse(url="/panel/categories", status_code=303)


# ──── Tags CRUD ───────────────────────────────────────────────────────────────


@router.get("/tags", response_class=HTMLResponse)
async def tags_page(
    request: Request,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    tags = await get_all_tags(db)
    return templates.TemplateResponse("panel/tags.html", {
        "request": request,
        "admin": admin,
        "active_page": "tags",
        "tags": tags,
        "flash_success": request.query_params.get("saved") and "Zapisano." or None,
    })


@router.post("/tags")
async def tag_create(
    request: Request,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    name = form.get("name", "").strip()
    slug = generate_slug(name)

    tag = Tag(name=name, slug=slug)
    db.add(tag)
    await db.commit()
    return RedirectResponse(url="/panel/tags?saved=1", status_code=303)


@router.post("/tags/{tag_id}/delete")
async def tag_delete(
    request: Request,
    tag_id: int,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if tag:
        await db.delete(tag)
        await db.commit()
    return RedirectResponse(url="/panel/tags", status_code=303)


# ──── Comments moderation ─────────────────────────────────────────────────────


@router.get("/comments", response_class=HTMLResponse)
async def comments_page(
    request: Request,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.article))
        .order_by(Comment.created_at.desc())
    )
    comments = list(result.scalars().all())
    return templates.TemplateResponse("panel/comments/list.html", {
        "request": request,
        "admin": admin,
        "active_page": "comments",
        "comments": comments,
    })


@router.post("/comments/{comment_id}/approve")
async def comment_approve(
    request: Request,
    comment_id: int,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if comment:
        comment.is_approved = True
        await db.commit()
    return RedirectResponse(url="/panel/comments", status_code=303)


@router.post("/comments/{comment_id}/hide")
async def comment_hide(
    request: Request,
    comment_id: int,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if comment:
        comment.is_approved = False
        await db.commit()
    return RedirectResponse(url="/panel/comments", status_code=303)


@router.post("/comments/{comment_id}/delete")
async def comment_delete(
    request: Request,
    comment_id: int,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if comment:
        await db.delete(comment)
        await db.commit()
    return RedirectResponse(url="/panel/comments", status_code=303)


# ──── Blacklist ───────────────────────────────────────────────────────────────


@router.get("/blacklist", response_class=HTMLResponse)
async def blacklist_page(
    request: Request,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BlacklistedWord).order_by(BlacklistedWord.word))
    words = list(result.scalars().all())
    return templates.TemplateResponse("panel/blacklist.html", {
        "request": request,
        "admin": admin,
        "active_page": "blacklist",
        "words": words,
    })


@router.post("/blacklist")
async def blacklist_add(
    request: Request,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    word = form.get("word", "").strip().lower()
    if word:
        db.add(BlacklistedWord(word=word))
        await db.commit()
    return RedirectResponse(url="/panel/blacklist", status_code=303)


@router.post("/blacklist/{word_id}/delete")
async def blacklist_delete(
    request: Request,
    word_id: int,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BlacklistedWord).where(BlacklistedWord.id == word_id))
    word = result.scalar_one_or_none()
    if word:
        await db.delete(word)
        await db.commit()
    return RedirectResponse(url="/panel/blacklist", status_code=303)


# ──── Media ───────────────────────────────────────────────────────────────────


@router.get("/media", response_class=HTMLResponse)
async def media_page(
    request: Request,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    media_list = await get_all_media(db)
    return templates.TemplateResponse("panel/media.html", {
        "request": request,
        "admin": admin,
        "active_page": "media",
        "media_list": media_list,
        "flash_success": request.query_params.get("uploaded") and "Plik przesłany." or None,
    })


@router.post("/media/upload")
async def media_upload(
    request: Request,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    file: UploadFile = form.get("file")
    alt_text = form.get("alt_text", "").strip() or None

    result = await upload_media(db, file, alt_text)
    if isinstance(result, str):
        media_list = await get_all_media(db)
        return templates.TemplateResponse("panel/media.html", {
            "request": request,
            "admin": admin,
            "active_page": "media",
            "media_list": media_list,
            "flash_error": result,
        })
    return RedirectResponse(url="/panel/media?uploaded=1", status_code=303)


@router.post("/media/{media_id}/delete")
async def media_delete_endpoint(
    request: Request,
    media_id: int,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await delete_media(db, media_id)
    return RedirectResponse(url="/panel/media", status_code=303)


# ──── Static pages ────────────────────────────────────────────────────────────


@router.get("/pages/{slug}/edit", response_class=HTMLResponse)
async def page_edit(
    request: Request,
    slug: str,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StaticPage).where(StaticPage.slug == slug))
    page = result.scalar_one_or_none()
    if not page:
        return RedirectResponse(url="/panel", status_code=303)

    return templates.TemplateResponse("panel/page_edit.html", {
        "request": request,
        "admin": admin,
        "active_page": "pages",
        "page": page,
        "flash_success": request.query_params.get("saved") and "Strona zapisana." or None,
    })


@router.post("/pages/{slug}")
async def page_update(
    request: Request,
    slug: str,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StaticPage).where(StaticPage.slug == slug))
    page = result.scalar_one_or_none()
    if not page:
        return RedirectResponse(url="/panel", status_code=303)

    form = await request.form()
    page.title = form.get("title", "").strip()
    page.content_md = form.get("content_md", "")
    page.content_html = render_markdown(page.content_md)
    page.meta_title = form.get("meta_title", "").strip() or None
    page.meta_description = form.get("meta_description", "").strip() or None
    await db.commit()
    return RedirectResponse(url=f"/panel/pages/{slug}/edit?saved=1", status_code=303)
