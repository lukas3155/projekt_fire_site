from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.article import Article, ArticleStatus
from app.models.category import Category
from app.models.static_page import StaticPage

router = APIRouter(tags=["seo"])


@router.get("/sitemap.xml", response_class=Response)
async def sitemap(request: Request, db: AsyncSession = Depends(get_db)):
    base = settings.SITE_URL

    urls = []

    # Static pages
    static_pages = [
        {"loc": f"{base}/blog", "priority": "1.0", "changefreq": "daily"},
        {"loc": f"{base}/tutaj-zacznij", "priority": "0.8", "changefreq": "weekly"},
        {"loc": f"{base}/o-mnie", "priority": "0.5", "changefreq": "monthly"},
        {"loc": f"{base}/kontakt", "priority": "0.3", "changefreq": "monthly"},
    ]
    urls.extend(static_pages)

    # Published articles
    result = await db.execute(
        select(Article)
        .where(Article.status == ArticleStatus.PUBLISHED)
        .order_by(Article.published_at.desc())
    )
    articles = result.scalars().all()
    for article in articles:
        lastmod = (article.updated_at or article.published_at or article.created_at).strftime("%Y-%m-%d")
        urls.append({
            "loc": f"{base}/{article.slug}",
            "lastmod": lastmod,
            "priority": "0.8",
            "changefreq": "weekly",
        })

    # Categories
    result = await db.execute(select(Category).order_by(Category.name))
    categories = result.scalars().all()
    for cat in categories:
        urls.append({
            "loc": f"{base}/kategoria/{cat.slug}",
            "priority": "0.6",
            "changefreq": "weekly",
        })

    # Build XML
    xml_entries = []
    for url in urls:
        entry = f"  <url>\n    <loc>{url['loc']}</loc>\n"
        if url.get("lastmod"):
            entry += f"    <lastmod>{url['lastmod']}</lastmod>\n"
        entry += f"    <changefreq>{url['changefreq']}</changefreq>\n"
        entry += f"    <priority>{url['priority']}</priority>\n"
        entry += "  </url>"
        xml_entries.append(entry)

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "\n".join(xml_entries)
    xml += "\n</urlset>"

    return Response(content=xml, media_type="application/xml")


@router.get("/robots.txt", response_class=Response)
async def robots_txt():
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /panel/\n"
        "Disallow: /htmx/\n"
        "\n"
        f"Sitemap: {settings.SITE_URL}/sitemap.xml\n"
    )
    return Response(content=content, media_type="text/plain")
