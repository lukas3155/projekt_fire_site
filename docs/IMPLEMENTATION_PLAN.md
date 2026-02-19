# Plan implementacji - Projekt FIRE

## Zasady

- Każda faza kończy się **działającym, testowalnym elementem**
- Fazy realizowane sekwencyjnie (każda zależy od poprzedniej)
- Kroki wewnątrz fazy mogą być realizowane równolegle tam, gdzie wskazano
- Po każdej fazie: commit + krótki test manualny

---

## Faza 1: Szkielet projektu

> **Cel:** Uruchomić pustą aplikację FastAPI w Dockerze z podłączoną bazą danych.

| # | Krok | Opis |
|---|------|------|
| 1.1 | Struktura katalogów | Utworzyć pełne drzewo katalogów zgodnie z ARCHITECTURE.md |
| 1.2 | requirements.txt | fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, jinja2, python-multipart, pydantic-settings, bcrypt, python-jose, markdown |
| 1.3 | .env.example + config.py | Pydantic Settings - wczytywanie konfiguracji z .env |
| 1.4 | database.py | Async engine SQLAlchemy + async session factory |
| 1.5 | app/main.py | FastAPI app factory, podpięcie Jinja2, montowanie /static, lifespan (startup/shutdown DB) |
| 1.6 | Dockerfile | Python 3.12-slim, install requirements, CMD uvicorn |
| 1.7 | docker-compose.yml | Serwisy: app (z hot reload) + db (postgres:16-alpine) |
| 1.8 | .gitignore | __pycache__, .env, uploads/, node_modules/, .idea/ |
| 1.9 | Alembic init | alembic init, konfiguracja env.py pod async SQLAlchemy |
| 1.10 | Weryfikacja | `docker-compose up` → FastAPI odpowiada na :8000, DB dostępna |

**Rezultat:** `docker-compose up` startuje FastAPI + PostgreSQL. Endpoint `/` zwraca "Projekt FIRE - w budowie".

---

## Faza 2: Modele bazy danych

> **Cel:** Zdefiniować wszystkie modele ORM i wygenerować migrację.

| # | Krok | Opis |
|---|------|------|
| 2.1 | models/category.py | Category (id, name, slug, description, created_at) |
| 2.2 | models/tag.py | Tag (id, name, slug, created_at) |
| 2.3 | models/article.py | Article + ArticleTag (association table). Pola: id, title, slug, content_md, content_html, excerpt, featured_image, category_id (FK), status (enum: draft/published), meta_title, meta_desc, og_image, created_at, updated_at, published_at, search_vector (TSVECTOR) |
| 2.4 | models/comment.py | Comment (id, article_id FK, nickname, content, is_approved, ip_address, created_at) |
| 2.5 | models/admin.py | AdminUser (id, username, password_hash, created_at) |
| 2.6 | models/media.py | Media (id, filename, original_name, file_path, file_size, mime_type, alt_text, created_at) |
| 2.7 | models/blacklisted_word.py | BlacklistedWord (id, word, created_at) |
| 2.8 | models/static_page.py | StaticPage (id, slug, title, content_md, content_html, meta_title, meta_desc, updated_at) |
| 2.9 | models/__init__.py | Import wszystkich modeli (potrzebne dla Alembic) |
| 2.10 | Migracja | `alembic revision --autogenerate` + `alembic upgrade head` |
| 2.11 | Trigger search_vector | Migracja SQL: trigger aktualizujący TSVECTOR przy INSERT/UPDATE na Article (konfiguracja `'polish'`) |
| 2.12 | Indeksy | GIN index na search_vector, composite index na (status, published_at), pozostałe indeksy wg ARCHITECTURE.md |
| 2.13 | scripts/seed.py | Skrypt tworzący: konto admina (bcrypt hash), przykładowe kategorie, przykładowy artykuł, strony statyczne (o-mnie) |
| 2.14 | Weryfikacja | Seed uruchomiony, dane widoczne w bazie (psql lub pgAdmin) |

**Rezultat:** Baza z pełnym schematem, przykładowymi danymi, indeksami i full-text search.

---

## Faza 3: Autentykacja admina

> **Cel:** Działający login/logout do panelu admina z session-based auth.

| # | Krok | Opis |
|---|------|------|
| 3.1 | utils/security.py | Funkcje: hash_password, verify_password (bcrypt), create_session, validate_session |
| 3.2 | services/auth_service.py | authenticate(username, password) → session cookie |
| 3.3 | Middleware auth | Dependency FastAPI: `get_current_admin` - sprawdza session cookie, redirect na login jeśli brak |
| 3.4 | routers/panel.py (login) | GET /panel/login → formularz, POST /panel/login → auth + redirect /panel |
| 3.5 | routers/panel.py (logout) | POST /panel/logout → usuń session → redirect /panel/login |
| 3.6 | Rate limiting logowania | Max 5 prób / 15 min / IP |
| 3.7 | templates/panel/login.html | Prosty formularz logowania (TailwindCSS) |
| 3.8 | Weryfikacja | Login z seed credentials → dostęp do /panel. Błędne hasło → odmowa. 6. próba → rate limit. |

**Rezultat:** Zabezpieczony panel admina z session-based auth.

---

## Faza 4: Panel admina - CRUD artykułów

> **Cel:** Pełne zarządzanie artykułami z edytorem Markdown.

| # | Krok | Opis |
|---|------|------|
| 4.1 | schemas/article.py | Pydantic schemas: ArticleCreate, ArticleUpdate, ArticleResponse |
| 4.2 | services/article_service.py | CRUD: create, get_by_id, get_list, update, delete. Markdown→HTML rendering. Generowanie slugów. |
| 4.3 | utils/markdown.py | Markdown → HTML z biblioteką `markdown` + rozszerzenia (fenced_code, tables, toc) |
| 4.4 | utils/seo.py | Funkcja generate_slug (polskie znaki → ASCII, unikalnośc) |
| 4.5 | templates/panel/base.html | Layout panelu: sidebar z nawigacją (Artykuły, Komentarze, Kategorie, Tagi, Media, Blacklista, Strony) |
| 4.6 | templates/panel/dashboard.html | Dashboard: liczba artykułów, komentarzy do moderacji, ostatnie wpisy |
| 4.7 | templates/panel/articles/list.html | Lista artykułów (tytuł, status, data, akcje) |
| 4.8 | templates/panel/articles/form.html | Formularz: tytuł, kategoria (select), tagi (multi-select), treść (EasyMDE - edytor Markdown), excerpt, featured image, meta title, meta description, status (draft/published) |
| 4.9 | Live preview | EasyMDE z wbudowanym podglądem Markdown |
| 4.10 | Endpointy CRUD | GET /panel/articles, GET /panel/articles/new, POST /panel/articles, GET /panel/articles/{id}/edit, PUT /panel/articles/{id}, DELETE /panel/articles/{id} |
| 4.11 | Weryfikacja | Utworzyć artykuł, edytować, podgląd Markdown, zmiana statusu draft→published, usunięcie |

**Rezultat:** Pełny CRUD artykułów z edytorem Markdown i podglądem.

---

## Faza 5: Panel admina - pozostałe moduły

> **Cel:** Zarządzanie kategoriami, tagami, komentarzami, blacklistą, mediami i stronami statycznymi.

| # | Krok | Opis |
|---|------|------|
| 5.1 | Kategorie CRUD | Endpointy + template. Formularz: nazwa, opis. Auto-generowanie sluga. |
| 5.2 | Tagi CRUD | Endpointy + template. Formularz: nazwa. Auto-generowanie sluga. |
| 5.3 | Moderacja komentarzy | Lista komentarzy (artykuł, nick, treść, data, IP). Akcje: usuń. Filtr: wszystkie / per artykuł. |
| 5.4 | Blacklista słów | Lista słów + formularz dodawania + usuwanie |
| 5.5 | services/media_service.py | Upload: walidacja mime type (tylko obrazki), generowanie UUID filename, zapis na dysk, zapis do DB. Usuwanie: plik + rekord DB. |
| 5.6 | Biblioteka mediów | Grid miniaturek, upload drag&drop (lub klasyczny input), kopiowanie URL do schowka, usuwanie |
| 5.7 | Edycja stron statycznych | GET /panel/pages/{slug}/edit → formularz Markdown. PUT /panel/pages/{slug} → zapis. Dotyczy strony "O mnie". |
| 5.8 | Weryfikacja | Przejść przez każdy moduł: dodać/edytować/usunąć kategorię, tag, słowo blacklisty. Upload obrazka. Edycja strony "O mnie". |

**Rezultat:** Kompletny panel administracyjny.

---

## Faza 6: Publiczny frontend - baza

> **Cel:** Bazowy layout, nawigacja, styl wizualny, TailwindCSS, HTMX.

| # | Krok | Opis |
|---|------|------|
| 6.1 | TailwindCSS setup | tailwind.config.js, input.css, build script (npx tailwindcss). Skonfigurować content paths na templates/**/*.html |
| 6.2 | templates/base.html | DOCTYPE, head (meta charset, viewport, TailwindCSS, HTMX), body structure, block content, block scripts |
| 6.3 | components/header.html | Logo "Projekt FIRE" + nawigacja: Blog, Tutaj zacznij, O mnie, Kontakt. Responsywne menu (hamburger na mobile). |
| 6.4 | components/footer.html | Linki social media (X, YouTube), copyright, rok |
| 6.5 | Paleta kolorów | Zdefiniować w tailwind.config.js: primary (zieleń/niebieski), neutral (szarości), accent. Minimalistyczny, jasny motyw. |
| 6.6 | Typografia | Czytelny font (system font stack lub Inter/Source Sans), duży font-size dla treści artykułów (18-20px) |
| 6.7 | Weryfikacja | Otworzyć stronę, nawigacja widoczna, responsywna na mobile, spójny styl wizualny |

**Rezultat:** Bazowy layout z nawigacją, gotowy do wypełnienia treścią.

---

## Faza 7: Publiczny frontend - strony treści

> **Cel:** Wszystkie publiczne strony z pełnym contentem.

| # | Krok | Opis |
|---|------|------|
| 7.1 | routers/blog.py | Router z endpointami: GET /, GET /blog, GET /blog/page/{number}, GET /{slug}, GET /kategoria/{slug}, GET /tag/{slug} |
| 7.2 | components/article_card.html | Karta artykułu: tytuł, excerpt, data, kategoria, tagi, featured image (opcjonalnie) |
| 7.3 | blog/list.html | Strona główna / lista artykułów. Grid kart artykułów + sidebar (kategorie, popularne tagi). |
| 7.4 | components/pagination.html | Numerowana paginacja: Poprzednia / 1 2 3 ... / Następna. URL: /blog/page/{n} |
| 7.5 | blog/detail.html | Pojedynczy artykuł: tytuł, data, kategoria, tagi, treść (rendered HTML), sekcja komentarzy |
| 7.6 | blog/category.html | Lista artykułów w kategorii (reuse article_card + pagination) |
| 7.7 | blog/tag.html | Lista artykułów z tagiem (reuse article_card + pagination) |
| 7.8 | routers/pages.py | Router: GET /tutaj-zacznij, GET /o-mnie, GET /kontakt, POST /kontakt |
| 7.9 | pages/start_here.html | "Tutaj zacznij" - lista artykułów z tagiem "beginner" z krótkim wstępem |
| 7.10 | pages/about.html | "O mnie" - treść z tabeli StaticPage (rendered HTML) |
| 7.11 | pages/contact.html | Formularz kontaktowy (imię, email, temat, treść) + linki social media + email |
| 7.12 | services/contact_service.py | Obsługa formularza: walidacja, rate limiting, wysłanie emaila (lub zapis do logów na start) |
| 7.13 | Weryfikacja | Przejść przez każdą stronę, sprawdzić linki, paginację, responsywność |

**Rezultat:** Wszystkie publiczne strony działają i wyświetlają treść z bazy.

---

## Faza 8: Wyszukiwarka i komentarze (HTMX)

> **Cel:** Interaktywne elementy strony bez przeładowania.

| # | Krok | Opis |
|---|------|------|
| 8.1 | routers/htmx.py | Router dla endpointów HTMX (zwracają partial HTML, nie pełne strony) |
| 8.2 | services/search_service.py | Full-text search: `plainto_tsquery('polish', query)` vs `search_vector`. Zwraca listę artykułów z rankingiem. |
| 8.3 | components/search_bar.html | Input z atrybutami HTMX: `hx-get="/htmx/search"`, `hx-trigger="keyup changed delay:300ms"`, `hx-target="#search-results"` |
| 8.4 | Endpoint GET /htmx/search | Przyjmuje `?q=...`, zwraca partial HTML z wynikami (article cards) |
| 8.5 | services/comment_service.py | create_comment (walidacja, spam check, zapis), get_comments_for_article |
| 8.6 | utils/spam.py | check_honeypot, check_rate_limit, check_blacklist. Zwraca (ok, error_message). |
| 8.7 | components/comment_form.html | Formularz: nick + treść + honeypot (ukryte pole). HTMX: `hx-post="/htmx/comments"`, `hx-target="#comments-list"`, `hx-swap="afterbegin"` |
| 8.8 | components/comment_list.html | Lista komentarzy (nick, data, treść). HTMX lazy load: `hx-get="/htmx/comments/{article_id}"`, `hx-trigger="load"` |
| 8.9 | Endpoint POST /htmx/comments | Walidacja → spam check → zapis → zwrot partial HTML nowego komentarza |
| 8.10 | Endpoint GET /htmx/comments/{article_id} | Zwraca partial HTML z listą komentarzy |
| 8.11 | Weryfikacja | Wpisać w wyszukiwarkę → wyniki pojawiają się live. Dodać komentarz → pojawia się bez przeładowania. Spam test → odrzucony. |

**Rezultat:** Wyszukiwarka live search + komentarze bez przeładowania strony.

---

## Faza 9: SEO

> **Cel:** Kompletna optymalizacja SEO.

| # | Krok | Opis |
|---|------|------|
| 9.1 | seo/meta.html | Template z meta tagami: title, description, canonical. Includowany w base.html. |
| 9.2 | seo/og.html | Open Graph: og:type, og:title, og:description, og:image, og:url, og:locale, og:site_name |
| 9.3 | seo/structured_data.html | JSON-LD: WebSite (strona główna), BlogPosting (artykuł), BreadcrumbList (breadcrumbs) |
| 9.4 | components/breadcrumbs.html | Nawigacja okruszkowa: Strona główna > Kategoria > Artykuł (z odpowiednimi linkami) |
| 9.5 | Sitemap.xml | Endpoint GET /sitemap.xml → dynamiczny XML ze wszystkimi opublikowanymi artykułami, kategoriami, stronami statycznymi. Priority + lastmod. |
| 9.6 | robots.txt | Plik statyczny: Allow /, Disallow /panel/, Sitemap: https://projektfire.pl/sitemap.xml |
| 9.7 | Kontekst SEO w routerach | Każdy route przekazuje do szablonu: page_title, page_description, canonical_url, og_image, og_type, breadcrumbs |
| 9.8 | Semantyczny HTML | Audit szablonów: poprawna hierarchia h1-h6, tagi <article>, <nav>, <main>, <aside>, <time datetime=""> |
| 9.9 | Lazy loading obrazków | Atrybut `loading="lazy"` na wszystkich obrazkach poza first viewport |
| 9.10 | Weryfikacja | Sprawdzić: meta tagi w źródle strony, Open Graph (debugger FB/Twitter), structured data (Google Rich Results Test), sitemap (walidator XML) |

**Rezultat:** Strona zoptymalizowana pod SEO, gotowa do indeksowania.

---

## Faza 10: Bezpieczeństwo i hardening

> **Cel:** Zabezpieczenie aplikacji przed typowymi atakami.

| # | Krok | Opis |
|---|------|------|
| 10.1 | CSRF | Token CSRF w każdym formularzu (POST). Walidacja po stronie serwera. |
| 10.2 | XSS | Sanityzacja treści komentarzy (html escape). Jinja2 domyślnie escapuje - upewnić się że `|safe` używane tylko dla zaufanego contentu (admin). |
| 10.3 | Rate limiting globalny | Middleware: konfigurowalny rate limit per endpoint (korzystając z slowapi lub custom) |
| 10.4 | Nagłówki bezpieczeństwa | Nginx: CSP, X-Frame-Options, X-Content-Type-Options, HSTS, Referrer-Policy |
| 10.5 | Walidacja uploadu | Sprawdzenie mime type (tylko image/*), max file size (np. 5MB), generowanie UUID filename (zapobieganie path traversal) |
| 10.6 | Input sanitization | Walidacja Pydantic na wszystkich endpointach: max length nicku, treści komentarza, pól formularza kontaktowego |
| 10.7 | Weryfikacja | Testy manualne: próba XSS w komentarzu, próba uploadu .php, próba brute-force logowania, sprawdzenie nagłówków (securityheaders.com) |

**Rezultat:** Aplikacja zabezpieczona przed OWASP Top 10.

---

## Faza 11: Infrastruktura produkcyjna

> **Cel:** Działający deployment na Hetzner VPS.

| # | Krok | Opis |
|---|------|------|
| 11.1 | Hetzner VPS | Zamówić CX22, Ubuntu 22.04, SSH key |
| 11.2 | Setup serwera | Zainstalować Docker + Docker Compose, ufw (firewall: 22, 80, 443), fail2ban |
| 11.3 | docker-compose.prod.yml | Serwisy: app, db, nginx. Sekrety z .env. Volumes: pgdata, uploads. Restart: always. |
| 11.4 | nginx/nginx.prod.conf | HTTPS redirect, SSL termination, proxy_pass do app, serwowanie /static i /uploads, gzip, security headers, cache headers |
| 11.5 | SSL / Let's Encrypt | Certbot: uzyskanie certyfikatu dla projektfire.pl, auto-renewal (cron) |
| 11.6 | Cloudflare | Dodać domenę, ustawić DNS A record → IP VPS, włączyć proxy (pomarańczowa chmurka), SSL mode: Full (Strict) |
| 11.7 | seohost DNS | Zmienić nameservery domeny na Cloudflare |
| 11.8 | Alembic migrate | Uruchomić migracje na produkcyjnej bazie |
| 11.9 | Seed admina | Uruchomić seed.py z produkcyjnym hasłem |
| 11.10 | Weryfikacja | Otworzyć https://projektfire.pl → strona działa, HTTPS, panel admina dostępny |

**Rezultat:** Strona live na https://projektfire.pl.

---

## Faza 12: CI/CD

> **Cel:** Automatyczny deploy po push do main.

| # | Krok | Opis |
|---|------|------|
| 12.1 | .github/workflows/deploy.yml | Workflow: trigger on push to main |
| 12.2 | Step: testy | `pytest` w kontenerze Docker |
| 12.3 | Step: build | Build Docker image |
| 12.4 | Step: deploy | SSH na VPS → git pull → docker-compose build → docker-compose up -d → alembic upgrade head |
| 12.5 | Step: health check | curl https://projektfire.pl → sprawdzić HTTP 200 |
| 12.6 | GitHub Secrets | Dodać: VPS_HOST, VPS_SSH_KEY, VPS_USER |
| 12.7 | Weryfikacja | Push do main → GitHub Actions → automatyczny deploy → strona zaktualizowana |

**Rezultat:** Push to main = automatyczny deploy.

---

## Faza 13: Testy i polish

> **Cel:** Upewnić się, że wszystko działa poprawnie.

| # | Krok | Opis |
|---|------|------|
| 13.1 | Testy jednostkowe | test_article_service, test_comment_service, test_search_service, test_spam, test_slug_generation |
| 13.2 | Testy integracyjne | test_blog_routes (lista, artykuł, kategoria, tag, paginacja), test_panel_routes (CRUD, auth), test_htmx (search, comments) |
| 13.3 | Test SEO | Google Rich Results Test, Lighthouse SEO audit, sprawdzenie sitemap, sprawdzenie robots.txt |
| 13.4 | Test wydajności | Lighthouse Performance score, sprawdzenie LCP < 2s, sprawdzenie rozmiarów obrazków |
| 13.5 | Test mobile | Sprawdzenie responsywności na różnych rozdzielczościach (Chrome DevTools) |
| 13.6 | Test bezpieczeństwa | securityheaders.com, próby XSS/CSRF, sprawdzenie rate limitingu |
| 13.7 | Test cross-browser | Chrome, Firefox, Safari (jeśli dostępne), Edge |
| 13.8 | Optymalizacja | Minifikacja CSS (TailwindCSS --minify), kompresja obrazków, cache headers |
| 13.9 | Weryfikacja końcowa | Przejście przez całą stronę jako czytelnik i jako admin - checklist akceptacyjny |

**Rezultat:** Strona przetestowana, zoptymalizowana, gotowa do publikacji treści.

---

## Podsumowanie faz

| Faza | Nazwa | Zależność |
|------|-------|-----------|
| 1 | Szkielet projektu | - |
| 2 | Modele bazy danych | Faza 1 |
| 3 | Autentykacja admina | Faza 2 |
| 4 | Panel admina - artykuły | Faza 3 |
| 5 | Panel admina - reszta | Faza 4 |
| 6 | Frontend - baza | Faza 1 |
| 7 | Frontend - strony | Faza 2 + 6 |
| 8 | Wyszukiwarka i komentarze | Faza 7 |
| 9 | SEO | Faza 7 |
| 10 | Bezpieczeństwo | Faza 8 |
| 11 | Infrastruktura prod | Faza 10 |
| 12 | CI/CD | Faza 11 |
| 13 | Testy i polish | Faza 12 |

```
Faza 1 ──→ Faza 2 ──→ Faza 3 ──→ Faza 4 ──→ Faza 5
  │                                              │
  └──→ Faza 6 ──→ Faza 7 ──→ Faza 8 ──→ Faza 9 ┘
                                │                │
                                └────→ Faza 10 ──┘
                                          │
                                       Faza 11 ──→ Faza 12 ──→ Faza 13
```

> **Uwaga:** Fazy 6-7 (frontend publiczny) mogą być realizowane równolegle z fazami 3-5 (panel admina) po ukończeniu fazy 2. W praktyce warto jednak najpierw mieć panel admina, żeby móc tworzyć treści do testowania frontendu publicznego.
