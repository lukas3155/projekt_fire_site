# PRD - Projekt FIRE (projektfire.pl)

## 1. Wizja produktu

Blog edukacyjny o tematyce finansowej, skierowany do osób rozpoczynających swoją drogę do niezależności finansowej (FIRE - Financial Independence, Retire Early). Strona ma służyć jako platforma do publikowania artykułów, poradników i materiałów edukacyjnych z zakresu oszczędzania, inwestowania i zarządzania finansami osobistymi.

**Domena:** projektfire.pl (zarejestrowana w seohost)
**Autor:** jednoosobowy blog

---

## 2. Grupa docelowa

- Osoby początkujące w temacie finansów osobistych i inwestowania
- Osoby z podstawowym doświadczeniem inwestycyjnym szukające pogłębienia wiedzy
- Wykluczona grupa: profesjonaliści z branży finansowej (treści nie są dla nich kierowane)

---

## 3. Struktura nawigacji

| Zakładka | Opis |
|----------|------|
| **Blog** | Lista wszystkich artykułów z filtrowaniem po kategoriach i tagach |
| **Tutaj zacznij** | Strona dla początkujących - filtrowana lista artykułów oznaczonych tagiem "beginner" |
| **O mnie** | Strona statyczna z informacjami o autorze |
| **Kontakt** | Formularz kontaktowy + linki do social media + adres email |

---

## 4. Wymagania funkcjonalne

### 4.1 System artykułów (Blog)

- **Kategorie** - każdy artykuł przypisany do kategorii (lista kategorii zarządzana z panelu admina, konkretne kategorie zostaną ustalone na etapie implementacji)
- **Tagi** - artykuły mogą mieć wiele tagów (w tym tag "beginner" wykorzystywany przez zakładkę "Tutaj zacznij")
- **Paginacja** - 10-12 artykułów na stronę, z numerowanymi stronami (każda strona ma unikalny URL dla SEO)
- **Wyszukiwarka** - full-text search po tytule i treści artykułów
- **Multimedia** - wsparcie dla obrazków, wykresów, infografik w treści artykułów
- **Embedy** - odnośniki/linki do materiałów YouTube (bez bezpośredniego osadzania na start)
- **Sortowanie** - domyślnie od najnowszych

### 4.2 System komentarzy

- Komentowanie **bez rejestracji** - użytkownik podaje nick przed wysłaniem komentarza
- **Zabezpieczenia antyspamowe:**
  - Rate limiting (ograniczenie liczby komentarzy z jednego IP w jednostce czasu)
  - Blacklista zakazanych słów (zarządzana z panelu admina)
  - Honeypot field (ukryte pole formularza łapiące boty)
- Komentarze wyświetlane pod artykułem
- Moderacja ręczna z poziomu panelu admina (zatwierdzanie/usuwanie)

### 4.3 Panel administracyjny

- **Autoryzacja:** login + hasło, dostęp tylko dla jednego użytkownika (autor)
- **Edytor artykułów:** edytor Markdown z podglądem na żywo (live preview)
- **Zarządzanie artykułami:** tworzenie, edycja, usuwanie, drafty (szkice), publikacja
- **Zarządzanie kategoriami i tagami:** CRUD
- **Moderacja komentarzy:** lista komentarzy oczekujących, zatwierdzanie, usuwanie
- **Blacklista słów:** dodawanie/usuwanie zakazanych słów
- **Zarządzanie mediami:** upload i przeglądanie obrazków/infografik

### 4.4 Strona "Kontakt"

- Formularz kontaktowy (imię, email, temat, treść wiadomości)
- Zabezpieczenie formularza przed spamem (honeypot + rate limiting)
- Linki do social media:
  - X (Twitter) - aktywne
  - YouTube - w przyszłości
- Adres email do kontaktu

### 4.5 Strona "O mnie"

- Strona statyczna z informacjami o autorze
- Edytowalna z poziomu panelu admina

### 4.6 Monetyzacja

- **Afiliacja** - możliwość umieszczania linków afiliacyjnych w treści artykułów
- Blog nie zawiera reklam (świadoma decyzja - autorytet i zaufanie czytelników)

### 4.7 Newsletter (przyszłość - poza MVP)

- Na etapie projektowania należy uwzględnić miejsce na formularz zapisu do newslettera
- Implementacja w przyszłości (formularz zapisu + integracja z serwisem mailingowym)
- Newsletter będzie darmowy

---

## 5. Wymagania niefunkcjonalne

### 5.1 SEO

SEO jest priorytetem. Wymagane elementy:

- **Server-Side Rendering** - cały HTML renderowany po stronie serwera (naturalnie zapewnione przez Jinja2)
- **Meta tagi** - title, description, keywords dla każdej strony i artykułu
- **Open Graph** - og:title, og:description, og:image dla poprawnego wyświetlania przy udostępnianiu w social media
- **Structured Data** - JSON-LD schema (Article, BlogPosting, BreadcrumbList, WebSite)
- **Sitemap.xml** - automatycznie generowana mapa strony
- **robots.txt** - poprawna konfiguracja
- **Canonical URLs** - zapobieganie duplikacji treści
- **Semantyczny HTML** - poprawna struktura nagłówków (h1-h6), tagi article, nav, main, aside
- **Szybkość ładowania** - optymalizacja obrazków (lazy loading, WebP), minifikacja CSS/JS
- **Mobile-first** - responsywny design, priorytet dla urządzeń mobilnych
- **Przyjazne URL** - slugi artykułów (np. `/blog/jak-zaczac-inwestowac`)
- **Breadcrumbs** - nawigacja okruszkowa
- **Alt text** - dla wszystkich obrazków

### 5.2 Wydajność

- Oczekiwany ruch na start: do kilkuset użytkowników dziennie
- Czas ładowania strony: < 2s (LCP)
- Optymalizacja obrazków po stronie serwera
- Cache na poziomie serwera (cache artykułów, cache wyszukiwarki)

### 5.3 Bezpieczeństwo

- HTTPS (certyfikat Let's Encrypt)
- Ochrona panelu admina (rate limiting logowania, bezpieczne przechowywanie hasła - bcrypt)
- Ochrona przed XSS (sanityzacja treści komentarzy)
- Ochrona przed CSRF (tokeny w formularzach)
- Ochrona przed SQL Injection (ORM - SQLAlchemy)
- Rate limiting na API
- Nagłówki bezpieczeństwa (CSP, X-Frame-Options, X-Content-Type-Options)
- Podstawowa ochrona DDoS (Cloudflare jako reverse proxy - darmowy plan)

### 5.4 Dostępność

- Responsywny design (mobile, tablet, desktop)
- Czytelna typografia (odpowiedni rozmiar fontów, kontrast)
- Nawigacja klawiaturą
- Semantyczny HTML

---

## 6. Stack technologiczny

### 6.1 Backend

| Komponent | Technologia |
|-----------|-------------|
| Framework | **FastAPI** (Python 3.12+) |
| ORM | **SQLAlchemy** (async) |
| Migracje | **Alembic** |
| Szablony | **Jinja2** (wbudowane w FastAPI) |
| Walidacja | **Pydantic** (wbudowane w FastAPI) |
| Serwer ASGI | **Uvicorn** |
| Autentykacja admina | **JWT** (lub session-based) |

### 6.2 Frontend

| Komponent | Technologia |
|-----------|-------------|
| Szablony HTML | **Jinja2** (server-side rendering) |
| Style | **TailwindCSS** |
| Interaktywność | **HTMX** |
| Edytor Markdown (admin) | Lekka biblioteka JS (np. EasyMDE) |

**Uzasadnienie:** Brak osobnego frameworka frontendowego (React/Vue). Szablony Jinja2 renderowane przez FastAPI zapewniają natywne SSR (kluczowe dla SEO), minimalizują ilość JS, i upraszczają deployment do jednego serwisu.

### 6.3 Baza danych

| Komponent | Technologia |
|-----------|-------------|
| Baza danych | **PostgreSQL 16** |
| Wyszukiwanie | **PostgreSQL Full-Text Search** (wbudowany, bez potrzeby Elasticsearch) |

**Uzasadnienie:** PostgreSQL oferuje wbudowany full-text search wystarczający dla bloga, lepsze wsparcie JSON, oraz jest standardem w ekosystemie Python/FastAPI.

### 6.4 Infrastruktura

| Komponent | Technologia |
|-----------|-------------|
| Serwer | **Hetzner VPS CX22** (2 vCPU, 4GB RAM, 40GB SSD, ~€4.51/mies.) |
| Konteneryzacja | **Docker** + **Docker Compose** |
| Reverse proxy | **Nginx** (lub Caddy) |
| SSL | **Let's Encrypt** (certbot lub Caddy auto-SSL) |
| DNS | **Cloudflare** (darmowy plan - DNS + podstawowa ochrona DDoS + cache) |
| Domena | **seohost** (tylko rejestracja domeny, DNS przekierowany na Cloudflare) |
| CI/CD | **GitHub Actions** (darmowe dla publicznych repo) |
| Monitoring | Podstawowy (logi Docker + opcjonalnie Uptime Kuma) |

### 6.5 Struktura Docker Compose

```
services:
  app        → FastAPI + Jinja2 + TailwindCSS (port 8000)
  db         → PostgreSQL 16 (port 5432, tylko wewnętrzny)
  nginx      → Reverse proxy + SSL termination (porty 80, 443)
```

---

## 7. Styl wizualny

- **Minimalistyczny** - czysty, czytelny layout typowy dla blogów finansowych
- **Jasny motyw** (z ewentualną opcją dark mode w przyszłości)
- **Typografia** - czytelna, duże fonty dla treści artykułów
- **Kolorystyka** - do ustalenia (sugestia: odcienie zieleni/niebieskiego kojarzone z finansami + neutralne szarości)
- **Layout:**
  - Header z logo + nawigacja
  - Główna kolumna treści
  - Sidebar (opcjonalny - popularne artykuły, kategorie)
  - Footer z linkami, social media, info o prawach autorskich

---

## 8. MVP vs Przyszłe funkcjonalności

### MVP (Wersja 1.0)

- [x] Strona główna z listą artykułów
- [x] System kategorii i tagów
- [x] Paginacja
- [x] Wyszukiwarka artykułów
- [x] Strona pojedynczego artykułu
- [x] System komentarzy (nick, antyspam)
- [x] Zakładka "Tutaj zacznij"
- [x] Strona "O mnie"
- [x] Strona "Kontakt" (formularz + social media)
- [x] Panel admina (artykuły, komentarze, kategorie, tagi)
- [x] SEO (meta tagi, sitemap, structured data, Open Graph)
- [x] Responsywny design
- [x] HTTPS + podstawowe zabezpieczenia
- [x] Deploy na Hetzner VPS z Docker Compose

### Przyszłe funkcjonalności (poza MVP)

- [ ] Newsletter (formularz zapisu + integracja z serwisem mailingowym)
- [ ] Dark mode
- [ ] Statystyki (integracja z Plausible/Umami zamiast Google Analytics - GDPR-friendly)
- [ ] Konto YouTube + embedy
- [ ] Cache na poziomie Cloudflare / Redis
- [ ] Zaawansowane statystyki admina (najpopularniejsze artykuły, ruch)

---

## 9. Ograniczenia i ryzyka

| Ryzyko | Mitygacja |
|--------|-----------|
| Niska znajomość frontendu | Stack Jinja2+Tailwind+HTMX minimalizuje potrzebę wiedzy frontendowej |
| SEO wymaga specjalistycznej wiedzy | Wbudowane mechanizmy SEO w architekturze + checklista do weryfikacji |
| Spam w komentarzach | Wielowarstwowa ochrona: honeypot + rate limiting + blacklista + moderacja ręczna |
| Wzrost ruchu ponad możliwości VPS | Łatwe skalowanie VPS na Hetzner + Cloudflare cache |
| Koszty hostingu | Hetzner CX22 (~20 PLN/mies.) daleko w limicie budżetu 100-150 PLN/mies. |

---

## 10. Budżet miesięczny

| Pozycja | Szacunkowy koszt |
|---------|-----------------|
| Hetzner VPS CX22 | ~20 PLN |
| Domena (seohost, roczny w przeliczeniu) | ~5-8 PLN |
| Cloudflare | 0 PLN (darmowy plan) |
| GitHub Actions | 0 PLN (darmowe) |
| **Razem** | **~25-28 PLN/mies.** |

Pozostaje duży zapas budżetu (~120 PLN) na ewentualne skalowanie lub dodatkowe usługi.
