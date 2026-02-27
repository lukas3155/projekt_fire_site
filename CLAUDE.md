# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Projekt FIRE (projektfire.pl) - a Polish-language blog about Financial Independence / Retire Early. Server-side rendered with FastAPI + Jinja2, styled with TailwindCSS, interactive via HTMX. PostgreSQL database with async SQLAlchemy ORM. Single admin user with session-based auth.

## Commands

### Development
```bash
docker-compose up              # Start dev environment (app + PostgreSQL, hot reload on :8000)
docker-compose down            # Stop containers
```

### Testing
Tests require the dev database to be running (`docker-compose up db`).
```bash
docker-compose exec app pytest                        # All tests
docker-compose exec app pytest tests/test_slug.py     # Single file
docker-compose exec app pytest -k test_homepage       # Single test
```

### Database Migrations
```bash
docker-compose exec app alembic upgrade head     # Apply migrations
docker-compose exec app alembic downgrade -1     # Rollback one
docker-compose exec app alembic revision --autogenerate -m "description"  # Create migration
```

### Seeding
```bash
docker-compose exec app python scripts/seed.py
```

### Production Deploy
Push to `main` triggers GitHub Actions → SSH to Hetzner VPS → `docker-compose.prod.yml` rebuild + migrate.

## Architecture

### Stack
- **Backend:** FastAPI 0.115.6, SQLAlchemy 2.0 (async), PostgreSQL 16, Alembic
- **Frontend:** Jinja2 templates (SSR), TailwindCSS, HTMX (vendored in `app/static/js/`)
- **Auth:** bcrypt + session cookies (not JWT for page auth), 24h TTL
- **Infra:** Docker Compose, Nginx reverse proxy, Let's Encrypt SSL, GitHub Actions CD

### Key Directories
```
app/
  main.py          # App factory, middleware, router registration
  config.py        # Pydantic settings from env vars / .env
  database.py      # SQLAlchemy async engine + session + Base
  middleware.py     # CSRF (double-submit cookie) + security headers
  templating.py    # Jinja2 environment config
  models/          # SQLAlchemy ORM models
  routers/         # FastAPI route handlers
  services/        # Business logic (article, auth, comment, search, media)
  schemas/         # Pydantic request/response models
  utils/           # Helpers (seo/slug, security, spam, markdown)
  templates/       # Jinja2 HTML (base.html, blog/, pages/, panel/, components/)
  static/          # CSS, JS, images, uploads
tests/             # pytest + pytest-asyncio, sync TestClient
alembic/           # DB migration versions
scripts/           # seed.py, deploy.sh, init-ssl.sh
nginx/             # Production nginx.prod.conf
```

### Router Registration Order (in main.py)
Order matters because `blog_router` contains the catch-all `/{slug}` route:
1. `panel_router` - `/panel/*` (admin CRUD, login, moderation)
2. `pages_router` - `/tutaj-zacznij`, `/o-mnie`, `/kontakt`, `/kalkulator-fire`, `/kalkulator-procent-skladany`
3. `htmx_router` - `/htmx/*` (search, comments via HTMX partials)
4. `seo_router` - `/sitemap.xml`, `/robots.txt`
5. `blog_router` - `/blog`, `/kategoria/{slug}`, `/tag/{slug}`, `/{slug}` (catch-all, must be last)

### Database Models & Relationships
- **Article** → belongs to **Category**, has many **Tag** (M2M via `ArticleTag`), has many **Comment**
- **Article** has `status` enum (DRAFT/SCHEDULED/PUBLISHED), `scheduled_publish_at` (nullable UTC datetime), `search_vector` column for PostgreSQL full-text search (GIN index). Background task in `app/main.py` checks every 60s for SCHEDULED articles past their `scheduled_publish_at` and auto-publishes them. Timezone conversion (Warsaw <-> UTC) handled in `app/routers/panel.py`.
- **StaticPage** - editable pages (about, contact, start-here) stored as Markdown + rendered HTML
- **BlacklistedWord** - spam filter wordlist checked against comments
- **Media** - uploaded file metadata
- All content entities use `slug` (UNIQUE) for URL routing

### Slug Generation
Polish diacritics are transliterated: ą→a, ć→c, ę→e, ł→l, ń→n, ó→o, ś→s, ź→z, ż→z. See `app/utils/seo.py`.

### Security Middleware
- `CSRFMiddleware` - double-submit cookie pattern on all state-changing requests
- `SecurityHeadersMiddleware` - X-Content-Type-Options, X-Frame-Options, Permissions-Policy
- Rate limiting is in-memory (per-IP dicts in `app/utils/security.py`)

### Testing Approach
- Sync `TestClient` (Starlette) with session scope to avoid asyncpg event loop issues
- Unit tests for slug generation, markdown rendering, spam detection, comment validation
- Integration tests for public HTTP routes (homepage, blog, 404 handling)

## Environment Variables

Configured via `app/config.py` (Pydantic `BaseSettings`), reads from env vars or `.env` file. See `.env.example` for development defaults. Key vars: `ENV`, `SECRET_KEY`, `DATABASE_URL`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `SITE_URL`, `SITE_NAME`, `CONTACT_EMAIL`.

## Design System

### Color Palette - monochromatic `fire` scale
The custom `fire` palette (defined in `base.html` Tailwind config) uses the Tailwind `neutral` gray scale - pure grays without blue tint. This matches the black-and-white Projekt FIRE logo.

```
fire-50:  #fafafa   - badge backgrounds, subtle highlights
fire-100: #f5f5f5
fire-200: #e5e5e5
fire-300: #d4d4d4
fire-400: #a3a3a3
fire-500: #737373   - focus rings
fire-600: #404040   - buttons, active pagination
fire-700: #262626   - links, headings, logo
fire-800: #171717   - footer background
fire-900: #0a0a0a   - darkest, hover states
```

### Semantic colors (NOT part of `fire`, kept as-is)
- **Red** (`text-red-600`, `bg-red-50`) - errors, delete actions
- **Yellow** (`bg-yellow-100`, `text-yellow-700`) - warnings, draft status

### Key style conventions
- **Header:** white background, `border-b border-gray-200`, sticky, height `h-20`
- **Footer:** dark (`bg-fire-800`), white headings, `text-gray-400` body, links hover to white
- **Article cards:** `border border-gray-100 shadow-sm`, `hover:shadow-md`, "Czytaj dalej" with `hover:underline`
- **Sidebar boxes:** same border+shadow pattern as cards
- **Buttons (public):** `bg-fire-600 hover:bg-fire-700 text-white`
- **Buttons (admin panel):** same `fire-600/700` pattern (previously green)
- **Focus rings:** `focus:ring-fire-500`
- **Inline content links** (article body, about page): `color: #262626`, `hover: #000000`, underlined with `text-underline-offset: 2px`
- **Blockquote border:** `#404040` (fire-600)
- **Body:** `leading-relaxed` for comfortable line-height, main content `py-10`
- **Admin panel links:** `text-fire-700 hover:text-fire-900` (previously blue/green)

### Style inspirations
Monochromatic design informed by Polish financial blog conventions (Inwestomat.eu, marciniwuc.com, finansowa.tv): dark footer, generous white space, subtle card borders, high line-height for readability.

## Admin Panel Patterns

### Article Form (`panel/articles/form.html`)
- **Editor:** EasyMDE (Markdown editor with live preview)
- **Media picker:** "Wybierz" button next to featured image input opens a modal with media grid. Clicking an image inserts `/static/uploads/{filename}` into the input and shows a preview thumbnail.
- **Publish/Unpublish/Schedule:** Dedicated buttons in sidebar (separate from "Zapisz zmiany") that POST to `/panel/articles/{id}/toggle-status`. Toggle handles 3 states: DRAFT->PUBLISHED, PUBLISHED->DRAFT, SCHEDULED->DRAFT. Also available as quick action on the article list.
- **Scheduled publishing:** Status dropdown has "Zaplanowany" option. Selecting it reveals a `datetime-local` input (Warsaw timezone) in an amber-highlighted box. The background task in `main.py` auto-publishes when the time arrives. Timezone helpers `_parse_scheduled_dt()` / `_utc_to_warsaw_input()` / `_utc_to_warsaw_display()` in `panel.py` convert between Warsaw and UTC.
- **Nested forms caveat:** The article form is one big `<form>`. Secondary actions (like toggle-status) that need their own POST must use a separate `<form>` placed **outside** the main form, triggered via `document.getElementById('form-id').submit()` from a `type="button"` button inside the main form. HTML does not allow nested `<form>` elements - the browser silently ignores the inner form.

### Panel routing convention
All admin panel state-changing routes use `POST` (not PUT/DELETE) because HTML forms only support GET/POST. Pattern: `POST /panel/{resource}/{id}/action` (e.g., `/toggle-status`, `/delete`, `/approve`).

## Conventions

- Use regular hyphens (`-`) instead of em-dashes in all files (code, templates, docs)
- All database operations use async SQLAlchemy sessions obtained via `get_db()` dependency
- Content stored as both Markdown (`content_md`) and pre-rendered HTML (`content_html`)
- Templates use Jinja2 autoescaping; HTMX endpoints return HTML partials (not JSON)
- Polish-language URL slugs and UI throughout
- FastAPI docs available at `/docs` only when `ENV=development`

## Calculators

Client-side financial tools (no backend needed, pure JS + Chart.js CDN).

### FIRE Calculator (`/kalkulator-fire`)
Template: `app/templates/pages/calculator_fire.html`

Inputs (each has synced `<input type="number">` + `<input type="range">`):
- Wiek obecny (18–70, default 30)
- Oczekiwana długość życia (60–100, default 85)
- Kapitał startowy (0–2 000 000 zł, default 50 000)
- Miesięczne oszczędności (0–25 000 zł, default 3 000)
- Roczny wzrost oszczędności (0–15%, default 0)
- Miesięczne wydatki (0–25 000 zł, default 5 000)
- Bezpieczna stopa wypłat / SWR (2–6%, default 4)
- Roczna stopa zwrotu nominalna (0–20%, default 8)
- Inflacja roczna (0–10%, default 3)

KPI cards: Twoja liczba FIRE, Lata do FIRE, Wiek FIRE, Stopa oszczędzania.
Chart: compound interest growth projection (real returns after inflation) with FIRE number line (Chart.js).

### Compound Interest Calculator (`/kalkulator-procent-skladany`)
Template: `app/templates/pages/calculator_compound.html`

Inputs (each has synced `<input type="number">` + `<input type="range">`, except compFreq which is `<select>`):
- Kapital poczatkowy (0-2 000 000 zl, default 10 000)
- Miesieczna wplata (0-25 000 zl, default 1 000)
- Roczny wzrost wplat (0-15%, default 0)
- Okres inwestowania (1-50 lat, default 20)
- Roczna stopa zwrotu (0-20%, default 7)
- Inflacja roczna (0-10%, default 3)
- Czestotliwosc kapitalizacji - select: Rocznie(1), Kwartalnie(4), Miesiecznie(12), Dziennie(365)

KPI cards: Wartosc koncowa (+ realna po inflacji), Suma wplat, Zysk z odsetek (+ realny), Mnoznik kapitalu.
Chart: stacked bar (Suma wplat + Odsetki) with two line overlays - nominal total and real (inflation-adjusted, dashed). Uses separate `yLine` axis (non-stacked, hidden) for lines to avoid Chart.js stacking issue with the bar `y` axis.

### Navigation
Header has a "Kalkulator" dropdown (CSS `group-hover` on desktop, JS toggle on mobile) linking to both calculators. Footer also lists both calculator links.
