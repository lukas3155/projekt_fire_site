# Architektura - Projekt FIRE (projektfire.pl)

## 1. Diagram ogólny

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────────────────────┐
│  Czytelnik  │─────▶│  Cloudflare  │─────▶│         Hetzner VPS             │
│  (Browser)  │◀─────│  (DNS+CDN)   │◀─────│                                 │
└─────────────┘      └──────────────┘      │  ┌───────────────────────────┐  │
                                           │  │  Nginx (reverse proxy)    │  │
┌─────────────┐                            │  │  :80 → redirect :443      │  │
│    Admin     │───── HTTPS ──────────────▶│  │  :443 → app:8000         │  │
│  (Browser)  │◀──────────────────────────│  │  + static files           │  │
└─────────────┘                            │  └───────────┬───────────────┘  │
                                           │              │                  │
                                           │  ┌───────────▼───────────────┐  │
                                           │  │  FastAPI + Jinja2 + HTMX  │  │
                                           │  │  (Uvicorn :8000)          │  │
                                           │  └───────────┬───────────────┘  │
                                           │              │                  │
                                           │  ┌───────────▼───────────────┐  │
                                           │  │  PostgreSQL 16            │  │
                                           │  │  (:5432, tylko internal)  │  │
                                           │  └───────────────────────────┘  │
                                           └─────────────────────────────────┘
```

**Przepływ żądania:**
1. Czytelnik wpisuje `projektfire.pl` w przeglądarce
2. DNS rozwiązywany przez Cloudflare (proxy + cache + DDoS protection)
3. Żądanie trafia na Nginx (SSL termination, serwowanie plików statycznych)
4. Nginx proxy-passuje do FastAPI (Uvicorn)
5. FastAPI renderuje szablon Jinja2 z danymi z PostgreSQL
6. Gotowy HTML wraca do przeglądarki

---

## 2. Struktura projektu

```
projekt_fire_site/
│
├── docs/
│   ├── PRD.md
│   └── ARCHITECTURE.md
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
├── .env.example
├── .gitignore
├── requirements.txt
│
├── nginx/
│   ├── nginx.conf
│   └── nginx.prod.conf
│
├── alembic/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app factory, middleware, startup/shutdown
│   ├── config.py                # Ustawienia (pydantic-settings, .env)
│   ├── database.py              # SQLAlchemy async engine + session
│   │
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── article.py
│   │   ├── category.py
│   │   ├── tag.py
│   │   ├── comment.py
│   │   ├── admin.py
│   │   ├── media.py
│   │   └── blacklisted_word.py
│   │
│   ├── schemas/                 # Pydantic schemas (walidacja request/response)
│   │   ├── __init__.py
│   │   ├── article.py
│   │   ├── comment.py
│   │   ├── category.py
│   │   ├── tag.py
│   │   └── admin.py
│   │
│   ├── routers/                 # FastAPI routers (endpointy)
│   │   ├── __init__.py
│   │   ├── blog.py              # Publiczne strony: artykuły, kategorie, tagi
│   │   ├── pages.py             # Statyczne strony: o-mnie, kontakt, tutaj-zacznij
│   │   ├── htmx.py              # Endpointy HTMX: wyszukiwarka, komentarze
│   │   └── panel.py             # Panel admina: CRUD artykułów, moderacja
│   │
│   ├── services/                # Logika biznesowa
│   │   ├── __init__.py
│   │   ├── article_service.py
│   │   ├── comment_service.py
│   │   ├── search_service.py
│   │   ├── media_service.py
│   │   └── auth_service.py
│   │
│   ├── templates/               # Szablony Jinja2
│   │   ├── base.html            # Bazowy layout (head, header, footer)
│   │   │
│   │   ├── blog/
│   │   │   ├── list.html        # Lista artykułów (strona główna)
│   │   │   ├── detail.html      # Pojedynczy artykuł
│   │   │   ├── category.html    # Artykuły w kategorii
│   │   │   └── tag.html         # Artykuły z tagiem
│   │   │
│   │   ├── pages/
│   │   │   ├── start_here.html  # Tutaj zacznij
│   │   │   ├── about.html       # O mnie
│   │   │   └── contact.html     # Kontakt
│   │   │
│   │   ├── panel/
│   │   │   ├── base.html        # Bazowy layout panelu admina
│   │   │   ├── login.html
│   │   │   ├── dashboard.html
│   │   │   ├── articles/
│   │   │   │   ├── list.html
│   │   │   │   ├── form.html    # Tworzenie + edycja (reużywalny)
│   │   │   │   └── preview.html
│   │   │   ├── comments/
│   │   │   │   └── list.html
│   │   │   ├── categories.html
│   │   │   ├── tags.html
│   │   │   ├── media.html
│   │   │   ├── blacklist.html
│   │   │   └── page_edit.html   # Edycja stron statycznych (O mnie)
│   │   │
│   │   ├── components/          # Reużywalne komponenty Jinja2
│   │   │   ├── header.html
│   │   │   ├── footer.html
│   │   │   ├── pagination.html
│   │   │   ├── article_card.html
│   │   │   ├── comment_form.html
│   │   │   ├── comment_list.html
│   │   │   ├── search_bar.html
│   │   │   ├── tag_cloud.html
│   │   │   └── breadcrumbs.html
│   │   │
│   │   └── seo/
│   │       ├── meta.html        # Meta tagi (include w base.html)
│   │       ├── og.html          # Open Graph tags
│   │       ├── structured_data.html  # JSON-LD schema
│   │       └── sitemap.xml      # Template sitemap
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── output.css       # Wygenerowany TailwindCSS
│   │   ├── js/
│   │   │   └── htmx.min.js      # HTMX (vendored)
│   │   ├── images/
│   │   │   ├── logo/
│   │   │   └── defaults/        # Domyślne obrazki (placeholder, og-image)
│   │   └── uploads/             # Uploadowane media (w PROD: volume Docker)
│   │
│   └── utils/
│       ├── __init__.py
│       ├── security.py          # Hashing, JWT, CSRF
│       ├── spam.py              # Honeypot, blacklista, rate limiting
│       ├── seo.py               # Generowanie slugów, sitemap, meta
│       ├── markdown.py          # Markdown → HTML rendering
│       └── pagination.py        # Helper paginacji
│
├── tests/
│   ├── conftest.py
│   ├── test_blog.py
│   ├── test_comments.py
│   ├── test_panel.py
│   ├── test_search.py
│   └── test_spam.py
│
└── scripts/
    ├── seed.py                  # Seed bazy (admin user, przykładowe dane)
    └── build_css.sh             # Build TailwindCSS
```

---

## 3. Baza danych - schemat

```
┌──────────────────────┐       ┌──────────────────────┐
│       Category       │       │         Tag          │
├──────────────────────┤       ├──────────────────────┤
│ id          PK       │       │ id          PK       │
│ name        VARCHAR  │       │ name        VARCHAR  │
│ slug        UNIQUE   │       │ slug        UNIQUE   │
│ description TEXT     │       │ created_at  TIMESTAMP│
│ created_at  TIMESTAMP│       └──────────┬───────────┘
└──────────┬───────────┘                  │
           │                              │
           │ 1:N                          │ N:M
           │                              │
┌──────────▼───────────┐       ┌──────────▼───────────┐
│       Article        │       │    ArticleTag        │
├──────────────────────┤       ├──────────────────────┤
│ id          PK       │◀──────│ article_id  FK       │
│ title       VARCHAR  │       │ tag_id      FK       │
│ slug        UNIQUE   │       │ (composite PK)       │
│ content_md  TEXT     │       └──────────────────────┘
│ content_html TEXT    │
│ excerpt     VARCHAR  │
│ featured_image VARCHAR│
│ category_id FK       │
│ status      ENUM     │  ← draft / scheduled / published
│ meta_title  VARCHAR  │
│ meta_desc   VARCHAR  │
│ og_image    VARCHAR  │
│ created_at  TIMESTAMP│
│ updated_at  TIMESTAMP│
│ published_at TIMESTAMP│
│ scheduled_publish_at TIMESTAMP│  ← nullable, UTC; kiedy auto-opublikowac
│ search_vector TSVECTOR│  ← PostgreSQL full-text search
└──────────┬───────────┘
           │
           │ 1:N
           │
┌──────────▼───────────┐
│       Comment        │
├──────────────────────┤
│ id          PK       │
│ article_id  FK       │
│ nickname    VARCHAR  │
│ content     TEXT     │
│ is_approved BOOLEAN  │  ← domyślnie TRUE (widoczne od razu)
│ ip_address  VARCHAR  │
│ created_at  TIMESTAMP│
└──────────────────────┘

┌──────────────────────┐
│      AdminUser       │
├──────────────────────┤
│ id          PK       │
│ username    UNIQUE   │
│ password_hash VARCHAR│
│ created_at  TIMESTAMP│
└──────────────────────┘

┌──────────────────────┐
│   BlacklistedWord    │
├──────────────────────┤
│ id          PK       │
│ word        VARCHAR  │
│ created_at  TIMESTAMP│
└──────────────────────┘

┌──────────────────────┐
│       Media          │
├──────────────────────┤
│ id          PK       │
│ filename    VARCHAR  │  ← UUID-based, unikalna nazwa na dysku
│ original_name VARCHAR│
│ file_path   VARCHAR  │
│ file_size   INTEGER  │
│ mime_type   VARCHAR  │
│ alt_text    VARCHAR  │
│ created_at  TIMESTAMP│
└──────────────────────┘

┌──────────────────────┐
│     StaticPage       │
├──────────────────────┤
│ id          PK       │
│ slug        UNIQUE   │  ← "o-mnie"
│ title       VARCHAR  │
│ content_md  TEXT     │
│ content_html TEXT    │
│ meta_title  VARCHAR  │
│ meta_desc   VARCHAR  │
│ updated_at  TIMESTAMP│
└──────────────────────┘
```

### Indeksy

| Tabela | Indeks | Typ | Cel |
|--------|--------|-----|-----|
| Article | `slug` | UNIQUE | Lookup artykułu po URL |
| Article | `status, published_at` | COMPOSITE | Lista opublikowanych, sortowana po dacie |
| Article | `category_id` | B-TREE | Filtrowanie po kategorii |
| Article | `search_vector` | GIN | Full-text search |
| Category | `slug` | UNIQUE | Lookup kategorii po URL |
| Tag | `slug` | UNIQUE | Lookup taga po URL |
| Comment | `article_id, created_at` | COMPOSITE | Komentarze pod artykułem, chronologicznie |
| Comment | `is_approved` | B-TREE | Filtrowanie komentarzy do moderacji |

### Full-Text Search

PostgreSQL `tsvector` + `GIN index` na tabeli Article:

```sql
-- Trigger aktualizujący search_vector przy INSERT/UPDATE
search_vector = to_tsvector('polish', coalesce(title, '') || ' ' || coalesce(content_md, ''))
```

Użycie konfiguracji językowej `'polish'` zapewnia poprawne stemming polskich słów.

---

## 4. Routing - mapa URL

### 4.1 Strony publiczne (HTML)

| Metoda | URL | Opis | Router |
|--------|-----|------|--------|
| GET | `/` | Redirect → `/blog` | `blog.py` |
| GET | `/blog` | Lista artykułów (strona główna) | `blog.py` |
| GET | `/blog/page/{number}` | Paginacja | `blog.py` |
| GET | `/{slug}` | Pojedynczy artykuł | `blog.py` |
| GET | `/kategoria/{slug}` | Artykuły w kategorii | `blog.py` |
| GET | `/tag/{slug}` | Artykuły z tagiem | `blog.py` |
| GET | `/tutaj-zacznij` | Strona "Tutaj zacznij" | `pages.py` |
| GET | `/o-mnie` | Strona "O mnie" | `pages.py` |
| GET | `/kontakt` | Strona "Kontakt" | `pages.py` |
| POST | `/kontakt` | Wysłanie formularza kontaktowego | `pages.py` |
| GET | `/sitemap.xml` | Sitemap | `blog.py` |
| GET | `/robots.txt` | Robots | static file |

### 4.2 Endpointy HTMX (partial HTML)

| Metoda | URL | Opis | Router |
|--------|-----|------|--------|
| GET | `/htmx/search?q=...` | Wyniki wyszukiwania (partial) | `htmx.py` |
| POST | `/htmx/comments` | Dodanie komentarza | `htmx.py` |
| GET | `/htmx/comments/{article_id}` | Lista komentarzy (partial) | `htmx.py` |

### 4.3 Panel administracyjny

| Metoda | URL | Opis | Router |
|--------|-----|------|--------|
| GET | `/panel/login` | Strona logowania | `panel.py` |
| POST | `/panel/login` | Autoryzacja | `panel.py` |
| POST | `/panel/logout` | Wylogowanie | `panel.py` |
| GET | `/panel` | Dashboard | `panel.py` |
| GET | `/panel/articles` | Lista artykułów | `panel.py` |
| GET | `/panel/articles/new` | Formularz nowego artykułu | `panel.py` |
| POST | `/panel/articles` | Zapisz nowy artykuł | `panel.py` |
| GET | `/panel/articles/{id}/edit` | Edycja artykułu | `panel.py` |
| PUT | `/panel/articles/{id}` | Aktualizuj artykuł | `panel.py` |
| POST | `/panel/articles/{id}/toggle-status` | Przełącz draft/scheduled/published | `panel.py` |
| DELETE | `/panel/articles/{id}` | Usuń artykuł | `panel.py` |
| GET | `/panel/comments` | Komentarze do moderacji | `panel.py` |
| DELETE | `/panel/comments/{id}` | Usuń komentarz | `panel.py` |
| GET | `/panel/categories` | Zarządzanie kategoriami | `panel.py` |
| POST | `/panel/categories` | Dodaj kategorię | `panel.py` |
| PUT | `/panel/categories/{id}` | Edytuj kategorię | `panel.py` |
| DELETE | `/panel/categories/{id}` | Usuń kategorię | `panel.py` |
| GET | `/panel/tags` | Zarządzanie tagami | `panel.py` |
| POST | `/panel/tags` | Dodaj tag | `panel.py` |
| DELETE | `/panel/tags/{id}` | Usuń tag | `panel.py` |
| GET | `/panel/blacklist` | Blacklista słów | `panel.py` |
| POST | `/panel/blacklist` | Dodaj słowo | `panel.py` |
| DELETE | `/panel/blacklist/{id}` | Usuń słowo | `panel.py` |
| POST | `/panel/media/upload` | Upload pliku | `panel.py` |
| GET | `/panel/media` | Biblioteka mediów | `panel.py` |
| DELETE | `/panel/media/{id}` | Usuń plik | `panel.py` |
| GET | `/panel/pages/{slug}/edit` | Edycja strony statycznej | `panel.py` |
| PUT | `/panel/pages/{slug}` | Aktualizuj stronę statyczną | `panel.py` |

### 4.4 Rozwiązanie konfliktu URL (płaska struktura)

Ponieważ artykuły i strony statyczne współdzielą root (`/`), routing musi rozróżniać:

```
Priorytet routingu:
1. Statyczne ścieżki: /blog, /kontakt, /o-mnie, /tutaj-zacznij, /panel/*
2. Prefiksy: /kategoria/*, /tag/*, /htmx/*
3. Fallback: /{slug} → szukaj artykułu w DB → jeśli brak → 404
```

Implementacja w FastAPI: statyczne strony rejestrowane jako osobne route'y z wyższym priorytetem. Route `/{slug}` zdefiniowany jako ostatni (catch-all).

---

## 5. Szablony - hierarchia i dziedziczenie

```
base.html
├── <head>
│   ├── {% include "seo/meta.html" %}
│   ├── {% include "seo/og.html" %}
│   ├── {% include "seo/structured_data.html" %}
│   ├── TailwindCSS
│   └── HTMX
├── <body>
│   ├── {% include "components/header.html" %}
│   ├── {% include "components/breadcrumbs.html" %}
│   ├── <main>{% block content %}{% endblock %}</main>
│   └── {% include "components/footer.html" %}
│
├── blog/list.html     → extends base.html
│   ├── components/search_bar.html
│   ├── components/article_card.html  (loop)
│   └── components/pagination.html
│
├── blog/detail.html   → extends base.html
│   ├── Treść artykułu (rendered HTML)
│   ├── components/tag_cloud.html
│   ├── components/comment_list.html   (HTMX: lazy load)
│   └── components/comment_form.html   (HTMX: submit)
│
└── panel/base.html    → OSOBNY layout (bez publicznego header/footer)
    ├── Sidebar nawigacja panelu
    └── {% block panel_content %}{% endblock %}
```

### Kluczowe decyzje szablonów

- **HTMX lazy loading komentarzy:** komentarze ładowane asynchronicznie po załadowaniu artykułu (szybsze LCP)
- **HTMX wyszukiwarka:** wyniki pojawiają się w trakcie wpisywania (debounce 300ms)
- **HTMX komentarz:** formularz wysyłany bez przeładowania strony, nowy komentarz pojawia się natychmiast
- **Panel admina ma osobny base.html** - zupełnie inny layout, nie dzieli CSS z publiczną stroną

---

## 6. Bezpieczeństwo - architektura

### 6.1 Autentykacja admina

```
Logowanie:
  POST /panel/login {username, password}
  → bcrypt verify(password, stored_hash)
  → Jeśli OK: ustaw session cookie (HttpOnly, Secure, SameSite=Strict)
  → Redirect /panel

Sesja:
  → Session-based auth (nie JWT - prostsze dla server-rendered app)
  → Cookie: httponly=True, secure=True, samesite=Strict, max_age=24h
  → Session data w bazie lub in-memory (wystarczające dla 1 usera)

Middleware:
  → Każdy request /panel/* (poza /panel/login) sprawdza session cookie
  → Brak sesji → redirect /panel/login
```

### 6.2 Ochrona antyspamowa komentarzy

```
Warstwa 1: Honeypot
  → Ukryte pole "website" w formularzu
  → Jeśli wypełnione → odrzuć (bot)

Warstwa 2: Rate limiting
  → Max 3 komentarze / IP / 10 minut
  → Implementacja: in-memory dict z TTL (lub Redis w przyszłości)

Warstwa 3: Blacklista słów
  → Sprawdzenie treści komentarza vs lista zakazanych słów
  → Jeśli zawiera → odrzuć z komunikatem

Warstwa 4: Moderacja ręczna (post-factum)
  → Komentarze widoczne od razu
  → Admin może usunąć z panelu
```

### 6.3 Rate limiting globalny

```
  → /panel/login: max 5 prób / 15 min / IP
  → /kontakt (POST): max 3 wysłania / godzina / IP
  → /htmx/comments (POST): max 3 / 10 min / IP
  → Reszta: bez limitu (Cloudflare obsługuje DDoS na wyższym poziomie)
```

### 6.4 Nagłówki bezpieczeństwa (Nginx)

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; img-src 'self' data:; ...
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

---

## 7. SEO - architektura

### 7.1 Meta tagi (w każdym szablonie)

```html
<!-- seo/meta.html -->
<title>{{ page_title }} | Projekt FIRE</title>
<meta name="description" content="{{ page_description }}">
<link rel="canonical" href="{{ canonical_url }}">
```

Każdy route przekazuje do szablonu: `page_title`, `page_description`, `canonical_url`.

### 7.2 Open Graph

```html
<!-- seo/og.html -->
<meta property="og:type" content="{{ og_type }}">  <!-- "article" lub "website" -->
<meta property="og:title" content="{{ page_title }}">
<meta property="og:description" content="{{ page_description }}">
<meta property="og:image" content="{{ og_image }}">
<meta property="og:url" content="{{ canonical_url }}">
<meta property="og:site_name" content="Projekt FIRE">
<meta property="og:locale" content="pl_PL">
```

### 7.3 Structured Data (JSON-LD)

```json
// Strona główna: WebSite + SearchAction
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Projekt FIRE",
  "url": "https://projektfire.pl",
  "potentialAction": {
    "@type": "SearchAction",
    "target": "https://projektfire.pl/htmx/search?q={search_term}",
    "query-input": "required name=search_term"
  }
}

// Artykuł: BlogPosting
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "...",
  "author": { "@type": "Person", "name": "..." },
  "datePublished": "...",
  "dateModified": "...",
  "image": "...",
  "description": "..."
}

// Breadcrumbs: BreadcrumbList
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [...]
}
```

### 7.4 Sitemap.xml

Automatycznie generowany endpoint zwracający XML ze wszystkimi:
- Opublikowanymi artykułami (z `lastmod` = `updated_at`)
- Stronami statycznymi
- Stronami kategorii
- Priorytetami (`homepage: 1.0`, `artykuł: 0.8`, `kategoria: 0.6`)

### 7.5 Przyjazne URL - slugi

```
Tytuł: "Jak zacząć inwestować w ETF-y?"
Slug:  "jak-zaczac-inwestowac-w-etf-y"

Reguły:
  → lowercase
  → polskie znaki → ASCII (ą→a, ę→e, ś→s, ...)
  → spacje i znaki specjalne → myślniki
  → usunięcie wielokrotnych myślników
  → unikalnośc (jeśli slug istnieje → dopisz -2, -3, ...)
```

---

## 8. Infrastruktura - Docker

### 8.1 docker-compose.yml (development)

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app          # Hot reload
      - ./uploads:/app/uploads
    environment:
      - DATABASE_URL=postgresql+asyncpg://fire:fire@db:5432/projektfire
      - ENV=development
      - SECRET_KEY=dev-secret-key
    depends_on:
      - db

  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=projektfire
      - POSTGRES_USER=fire
      - POSTGRES_PASSWORD=fire
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

### 8.2 docker-compose.prod.yml (production)

```yaml
services:
  app:
    build: .
    restart: always
    environment:
      - DATABASE_URL=postgresql+asyncpg://fire:${DB_PASSWORD}@db:5432/projektfire
      - ENV=production
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db

  db:
    image: postgres:16-alpine
    restart: always
    environment:
      - POSTGRES_DB=projektfire
      - POSTGRES_USER=fire
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
      - ./app/static:/var/www/static        # Nginx serwuje static files
      - uploads:/var/www/uploads
    depends_on:
      - app

  certbot:
    image: certbot/certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot

volumes:
  pgdata:
  uploads:
```

### 8.3 Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build TailwindCSS (w produkcji)
RUN npx tailwindcss -i ./app/static/css/input.css -o ./app/static/css/output.css --minify

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 8.4 Nginx (production)

```
Kluczowe reguły:
  → Redirect HTTP → HTTPS
  → SSL termination (Let's Encrypt)
  → Proxy pass / → app:8000
  → Serwowanie /static/* bezpośrednio z dysku (bypass FastAPI)
  → Serwowanie /uploads/* bezpośrednio z dysku
  → Gzip compression
  → Cache headers dla static files (1 rok)
  → Nagłówki bezpieczeństwa
```

---

## 9. CI/CD - GitHub Actions

```
Workflow: deploy.yml
Trigger: push to main

Steps:
  1. Checkout kodu
  2. Uruchom testy (pytest)
  3. Build Docker image
  4. SSH na Hetzner VPS
  5. Pull nowy image
  6. docker-compose -f docker-compose.prod.yml up -d
  7. Alembic migrate (jeśli nowe migracje)
  8. Health check
```

---

## 10. Konfiguracja (.env)

```env
# Application
ENV=production
SECRET_KEY=<random-64-char-string>
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<bcrypt-hash>

# Database
DATABASE_URL=postgresql+asyncpg://fire:<password>@db:5432/projektfire

# Contact form
CONTACT_EMAIL=kontakt@projektfire.pl

# Domain
SITE_URL=https://projektfire.pl
SITE_NAME=Projekt FIRE
```
