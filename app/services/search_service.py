from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article, ArticleStatus


async def search_articles(session: AsyncSession, query: str, limit: int = 10) -> list[Article]:
    """Full-text search on articles using PostgreSQL tsvector."""
    if not query or not query.strip():
        return []

    search_query = query.strip()

    result = await session.execute(
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.tags))
        .where(
            Article.status == ArticleStatus.PUBLISHED,
            Article.search_vector.op("@@")(func.plainto_tsquery("simple", search_query)),
        )
        .order_by(
            func.ts_rank(Article.search_vector, func.plainto_tsquery("simple", search_query)).desc()
        )
        .limit(limit)
    )
    return list(result.scalars().all())
