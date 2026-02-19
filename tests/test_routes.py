"""Integration tests for public routes.

These tests use the actual database connection (dev DB must be running).
"""


def test_homepage_redirects_to_blog(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/blog"


def test_blog_page(client):
    response = client.get("/blog")
    assert response.status_code == 200
    assert "Blog" in response.text


def test_blog_pagination_page_1_redirects(client):
    response = client.get("/blog/page/1", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/blog"


def test_start_here_page(client):
    response = client.get("/tutaj-zacznij")
    assert response.status_code == 200
    assert "Tutaj zacznij" in response.text


def test_contact_page(client):
    response = client.get("/kontakt")
    assert response.status_code == 200
    assert "Kontakt" in response.text


def test_404_page(client):
    response = client.get("/nonexistent-slug-that-does-not-exist")
    assert response.status_code == 404


def test_sitemap(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert "urlset" in response.text
    assert "application/xml" in response.headers["content-type"]


def test_robots_txt(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert "Disallow: /panel/" in response.text
    assert "Sitemap:" in response.text


def test_panel_login_page(client):
    response = client.get("/panel/login")
    assert response.status_code == 200
    assert "Zaloguj" in response.text


def test_panel_requires_auth(client):
    response = client.get("/panel", follow_redirects=False)
    assert response.status_code == 303
    assert "/panel/login" in response.headers["location"]


def test_search_endpoint(client):
    response = client.get("/htmx/search?q=test")
    assert response.status_code == 200


def test_security_headers(client):
    response = client.get("/blog")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


def test_csrf_blocks_without_token(client):
    response = client.post("/kontakt", data={
        "name": "Test",
        "email": "test@test.com",
        "subject": "Test",
        "message": "Hello",
    })
    assert response.status_code == 403
