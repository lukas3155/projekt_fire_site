from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.comment_service import create_comment, get_comments_for_article
from app.services.search_service import search_articles
from app.templating import templates
from app.utils.spam import (
    check_blacklist,
    check_comment_rate_limit,
    check_honeypot,
    record_comment_attempt,
)

router = APIRouter(prefix="/htmx", tags=["htmx"])


@router.get("/search", response_class=HTMLResponse)
async def htmx_search(
    request: Request,
    q: str = "",
    db: AsyncSession = Depends(get_db),
):
    articles = await search_articles(db, q) if q.strip() else []
    return templates.TemplateResponse("components/search_results.html", {
        "request": request,
        "articles": articles,
        "query": q.strip(),
    })


@router.get("/comments/{article_id}", response_class=HTMLResponse)
async def htmx_comments_list(
    request: Request,
    article_id: int,
    db: AsyncSession = Depends(get_db),
):
    comments = await get_comments_for_article(db, article_id)
    return templates.TemplateResponse("components/comment_list.html", {
        "request": request,
        "comments": comments,
        "article_id": article_id,
    })


@router.post("/comments", response_class=HTMLResponse)
async def htmx_comment_create(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    client_ip = request.client.host if request.client else "unknown"

    # Honeypot
    if check_honeypot(form.get("website")):
        return HTMLResponse("")

    article_id = int(form.get("article_id", 0))
    nickname = form.get("nickname", "").strip()
    content = form.get("content", "").strip()

    # Validation
    if not nickname or not content or not article_id:
        return HTMLResponse(
            '<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-3 text-sm">'
            'Wypełnij wszystkie pola.</div>',
            status_code=422,
            headers={"HX-Retarget": "#comment-errors", "HX-Reswap": "innerHTML"},
        )

    if len(nickname) > 100 or len(content) > 2000:
        return HTMLResponse(
            '<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-3 text-sm">'
            'Nick (max 100 znaków) lub komentarz (max 2000 znaków) jest za długi.</div>',
            status_code=422,
            headers={"HX-Retarget": "#comment-errors", "HX-Reswap": "innerHTML"},
        )

    # Rate limit
    if not check_comment_rate_limit(client_ip):
        return HTMLResponse(
            '<div class="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded mb-3 text-sm">'
            'Zbyt wiele komentarzy. Spróbuj za kilka minut.</div>',
            status_code=429,
            headers={"HX-Retarget": "#comment-errors", "HX-Reswap": "innerHTML"},
        )

    # Blacklist
    matched_word = await check_blacklist(db, content)
    if matched_word:
        return HTMLResponse(
            '<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-3 text-sm">'
            'Komentarz zawiera niedozwolone treści.</div>',
            status_code=422,
            headers={"HX-Retarget": "#comment-errors", "HX-Reswap": "innerHTML"},
        )

    matched_word = await check_blacklist(db, nickname)
    if matched_word:
        return HTMLResponse(
            '<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-3 text-sm">'
            'Nick zawiera niedozwolone treści.</div>',
            status_code=422,
            headers={"HX-Retarget": "#comment-errors", "HX-Reswap": "innerHTML"},
        )

    record_comment_attempt(client_ip)

    comment = await create_comment(
        db,
        article_id=article_id,
        nickname=nickname,
        content=content,
        ip_address=client_ip,
    )

    return templates.TemplateResponse("components/comment_single.html", {
        "request": request,
        "comment": comment,
    })
