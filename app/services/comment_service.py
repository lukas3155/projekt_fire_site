from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment


async def get_comments_for_article(session: AsyncSession, article_id: int) -> list[Comment]:
    result = await session.execute(
        select(Comment)
        .where(Comment.article_id == article_id, Comment.is_approved == True)
        .order_by(Comment.created_at.asc())
    )
    return list(result.scalars().all())


async def create_comment(
    session: AsyncSession,
    *,
    article_id: int,
    nickname: str,
    content: str,
    ip_address: str | None = None,
) -> Comment:
    comment = Comment(
        article_id=article_id,
        nickname=nickname,
        content=content,
        ip_address=ip_address,
        is_approved=True,
    )
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return comment
