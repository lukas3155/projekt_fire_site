from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article, ArticleStatus, article_tag
from app.models.category import Category
from app.models.tag import Tag
from app.utils.markdown import render_markdown
from app.utils.seo import generate_slug


async def get_articles(
    session: AsyncSession,
    *,
    status: ArticleStatus | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Article], int]:
    """Get paginated articles. Returns (articles, total_count)."""
    query = select(Article).options(selectinload(Article.category), selectinload(Article.tags))

    if status:
        query = query.where(Article.status == status)

    # Count
    count_query = select(func.count(Article.id))
    if status:
        count_query = count_query.where(Article.status == status)
    total = (await session.execute(count_query)).scalar() or 0

    # Fetch page
    query = query.order_by(Article.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await session.execute(query)
    articles = list(result.scalars().all())

    return articles, total


async def get_article_by_id(session: AsyncSession, article_id: int) -> Article | None:
    result = await session.execute(
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.tags))
        .where(Article.id == article_id)
    )
    return result.scalar_one_or_none()


async def _ensure_unique_slug(session: AsyncSession, slug: str, exclude_id: int | None = None) -> str:
    """Ensure slug is unique, appending -2, -3, etc. if needed."""
    base_slug = slug
    counter = 1
    while True:
        query = select(Article.id).where(Article.slug == slug)
        if exclude_id:
            query = query.where(Article.id != exclude_id)
        result = await session.execute(query)
        if result.scalar_one_or_none() is None:
            return slug
        counter += 1
        slug = f"{base_slug}-{counter}"


async def _resolve_tags(session: AsyncSession, tag_ids: list[int]) -> list[Tag]:
    if not tag_ids:
        return []
    result = await session.execute(select(Tag).where(Tag.id.in_(tag_ids)))
    return list(result.scalars().all())


async def create_article(
    session: AsyncSession,
    *,
    title: str,
    content_md: str,
    excerpt: str | None = None,
    featured_image: str | None = None,
    category_id: int | None = None,
    tag_ids: list[int] | None = None,
    status: ArticleStatus = ArticleStatus.DRAFT,
    meta_title: str | None = None,
    meta_description: str | None = None,
    scheduled_publish_at: datetime | None = None,
) -> Article:
    slug = await _ensure_unique_slug(session, generate_slug(title))
    content_html = render_markdown(content_md)

    article = Article(
        title=title,
        slug=slug,
        content_md=content_md,
        content_html=content_html,
        excerpt=excerpt,
        featured_image=featured_image,
        category_id=category_id,
        status=status,
        meta_title=meta_title,
        meta_description=meta_description,
    )

    if status == ArticleStatus.PUBLISHED:
        article.published_at = datetime.utcnow()

    if status == ArticleStatus.SCHEDULED:
        article.scheduled_publish_at = scheduled_publish_at
    else:
        article.scheduled_publish_at = None

    article.tags = await _resolve_tags(session, tag_ids or [])

    session.add(article)
    await session.commit()
    await session.refresh(article)
    return article


async def update_article(
    session: AsyncSession,
    article: Article,
    *,
    title: str,
    content_md: str,
    excerpt: str | None = None,
    featured_image: str | None = None,
    category_id: int | None = None,
    tag_ids: list[int] | None = None,
    status: ArticleStatus = ArticleStatus.DRAFT,
    meta_title: str | None = None,
    meta_description: str | None = None,
    scheduled_publish_at: datetime | None = None,
) -> Article:
    article.title = title
    article.content_md = content_md
    article.content_html = render_markdown(content_md)
    article.excerpt = excerpt
    article.featured_image = featured_image
    article.category_id = category_id
    article.status = status
    article.meta_title = meta_title
    article.meta_description = meta_description
    article.updated_at = datetime.utcnow()

    # Update slug only if title changed
    new_slug = generate_slug(title)
    if new_slug != article.slug:
        article.slug = await _ensure_unique_slug(session, new_slug, exclude_id=article.id)

    # Handle published_at
    if status == ArticleStatus.PUBLISHED and article.published_at is None:
        article.published_at = datetime.utcnow()

    # Handle scheduled_publish_at
    if status == ArticleStatus.SCHEDULED:
        article.scheduled_publish_at = scheduled_publish_at
    else:
        article.scheduled_publish_at = None

    article.tags = await _resolve_tags(session, tag_ids or [])

    await session.commit()
    await session.refresh(article)
    return article


async def delete_article(session: AsyncSession, article: Article) -> None:
    await session.delete(article)
    await session.commit()


async def get_all_categories(session: AsyncSession) -> list[Category]:
    result = await session.execute(select(Category).order_by(Category.name))
    return list(result.scalars().all())


async def get_all_tags(session: AsyncSession) -> list[Tag]:
    result = await session.execute(select(Tag).order_by(Tag.name))
    return list(result.scalars().all())


async def publish_scheduled_articles(session: AsyncSession) -> int:
    """Publish articles whose scheduled_publish_at has passed. Returns count."""
    now = datetime.utcnow()
    result = await session.execute(
        select(Article).where(
            Article.status == ArticleStatus.SCHEDULED,
            Article.scheduled_publish_at <= now,
        )
    )
    articles = list(result.scalars().all())
    for article in articles:
        article.status = ArticleStatus.PUBLISHED
        article.published_at = now
        article.scheduled_publish_at = None
    if articles:
        await session.commit()
    return len(articles)
