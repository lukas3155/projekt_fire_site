from app.utils.spam import check_comment_rate_limit, check_honeypot, record_comment_attempt


def test_honeypot_empty():
    assert check_honeypot("") is False
    assert check_honeypot(None) is False


def test_honeypot_filled():
    assert check_honeypot("spam-site.com") is True
    assert check_honeypot("anything") is True


def test_rate_limit_allows_initial():
    # Use a unique IP to avoid test interference
    assert check_comment_rate_limit("test-unique-ip-1") is True


def test_rate_limit_blocks_after_max():
    ip = "test-rate-limit-ip"
    for _ in range(3):
        record_comment_attempt(ip)
    assert check_comment_rate_limit(ip) is False
