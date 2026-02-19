import enum
from datetime import datetime

from sqlalchemy import Column, Enum, ForeignKey, Index, Integer, String, Table, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ArticleStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


article_tag = Table(
    "article_tags",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(350), unique=True, nullable=False, index=True)
    content_md: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_html: Mapped[str] = mapped_column(Text, nullable=False, default="")
    excerpt: Mapped[str | None] = mapped_column(String(500), nullable=True)
    featured_image: Mapped[str | None] = mapped_column(String(500), nullable=True)

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )

    status: Mapped[ArticleStatus] = mapped_column(
        Enum(ArticleStatus), nullable=False, default=ArticleStatus.DRAFT
    )

    meta_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    og_image: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)

    search_vector = mapped_column(TSVECTOR, nullable=True)

    category: Mapped["Category"] = relationship(back_populates="articles")  # noqa: F821
    tags: Mapped[list["Tag"]] = relationship(secondary=article_tag, lazy="selectin")  # noqa: F821
    comments: Mapped[list["Comment"]] = relationship(back_populates="article", cascade="all, delete-orphan")  # noqa: F821

    __table_args__ = (
        Index("ix_articles_status_published", "status", "published_at"),
        Index("ix_articles_search_vector", "search_vector", postgresql_using="gin"),
    )
