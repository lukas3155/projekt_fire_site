import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "uploads"
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


async def get_all_media(session: AsyncSession) -> list[Media]:
    result = await session.execute(select(Media).order_by(Media.created_at.desc()))
    return list(result.scalars().all())


async def upload_media(
    session: AsyncSession,
    file: UploadFile,
    alt_text: str | None = None,
) -> Media | str:
    """Upload a file. Returns Media on success or error message string."""
    if file.content_type not in ALLOWED_MIME_TYPES:
        return "Niedozwolony typ pliku. Dozwolone: JPEG, PNG, GIF, WebP, SVG."

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        return f"Plik zbyt duży. Maksymalny rozmiar: {MAX_FILE_SIZE // (1024*1024)} MB."

    ext = os.path.splitext(file.filename or "file")[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_DIR / unique_name
    with open(file_path, "wb") as f:
        f.write(content)

    media = Media(
        filename=unique_name,
        original_name=file.filename or "file",
        file_path=str(file_path),
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        alt_text=alt_text,
    )
    session.add(media)
    await session.commit()
    return media


async def delete_media(session: AsyncSession, media_id: int) -> bool:
    result = await session.execute(select(Media).where(Media.id == media_id))
    media = result.scalar_one_or_none()
    if not media:
        return False

    file_path = UPLOAD_DIR / media.filename
    if file_path.exists():
        file_path.unlink()

    await session.delete(media)
    await session.commit()
    return True
