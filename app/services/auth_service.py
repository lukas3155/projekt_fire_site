from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import AdminUser
from app.utils.security import verify_password


async def authenticate_admin(session: AsyncSession, username: str, password: str) -> AdminUser | None:
    result = await session.execute(
        select(AdminUser).where(AdminUser.username == username)
    )
    admin = result.scalar_one_or_none()

    if admin is None or not verify_password(password, admin.password_hash):
        return None

    return admin
