"""Seed script - creates admin user, sample categories, tags, and static pages."""
import asyncio

import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models.admin import AdminUser
from app.models.category import Category
from app.models.static_page import StaticPage
from app.models.tag import Tag


async def seed():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # Check if already seeded
        result = await session.execute(text("SELECT COUNT(*) FROM admin_users"))
        count = result.scalar()
        if count > 0:
            print("Database already seeded. Skipping.")
            await engine.dispose()
            return

        # Create admin user
        password_hash = bcrypt.hashpw(
            settings.ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        admin = AdminUser(
            username=settings.ADMIN_USERNAME,
            password_hash=password_hash,
        )
        session.add(admin)

        # Create sample categories
        categories = [
            Category(name="Oszczędzanie", slug="oszczedzanie", description="Porady dotyczące oszczędzania pieniędzy"),
            Category(name="Inwestowanie", slug="inwestowanie", description="Podstawy i strategie inwestowania"),
            Category(name="FIRE", slug="fire", description="Niezależność finansowa i wczesna emerytura"),
            Category(name="Budżet domowy", slug="budzet-domowy", description="Zarządzanie budżetem domowym"),
        ]
        session.add_all(categories)

        # Create sample tags
        tags = [
            Tag(name="beginner", slug="beginner"),
            Tag(name="ETF", slug="etf"),
            Tag(name="giełda", slug="gielda"),
            Tag(name="konto maklerskie", slug="konto-maklerskie"),
            Tag(name="poduszka finansowa", slug="poduszka-finansowa"),
            Tag(name="IKE/IKZE", slug="ike-ikze"),
        ]
        session.add_all(tags)

        # Create static pages
        about_page = StaticPage(
            slug="o-mnie",
            title="O mnie",
            content_md="# O mnie\n\nTutaj pojawi się opis autora bloga Projekt FIRE.",
            content_html="<h1>O mnie</h1>\n<p>Tutaj pojawi się opis autora bloga Projekt FIRE.</p>",
            meta_title="O mnie | Projekt FIRE",
            meta_description="Poznaj autora bloga Projekt FIRE - o niezależności finansowej i inwestowaniu.",
        )
        session.add(about_page)

        # Create full-text search trigger
        await session.execute(text("""
            CREATE OR REPLACE FUNCTION articles_search_vector_update() RETURNS trigger AS $$
            BEGIN
                NEW.search_vector :=
                    to_tsvector('simple', coalesce(NEW.title, '')) ||
                    to_tsvector('simple', coalesce(NEW.content_md, ''));
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))

        await session.execute(text("""
            DROP TRIGGER IF EXISTS articles_search_vector_trigger ON articles;
        """))

        await session.execute(text("""
            CREATE TRIGGER articles_search_vector_trigger
                BEFORE INSERT OR UPDATE ON articles
                FOR EACH ROW
                EXECUTE FUNCTION articles_search_vector_update();
        """))

        await session.commit()
        print("Seed completed successfully!")
        print(f"  Admin user: {settings.ADMIN_USERNAME}")
        print(f"  Categories: {len(categories)}")
        print(f"  Tags: {len(tags)}")
        print(f"  Static pages: 1 (O mnie)")
        print(f"  Full-text search trigger: created")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
