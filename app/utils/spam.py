import time
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blacklisted_word import BlacklistedWord

# Rate limiting: {ip: [timestamp, ...]}
_comment_attempts: dict[str, list[float]] = defaultdict(list)
COMMENT_RATE_LIMIT = 3
COMMENT_RATE_WINDOW = 600  # 10 minutes


def check_honeypot(value: str | None) -> bool:
    """Returns True if honeypot was triggered (is a bot)."""
    return bool(value)


def check_comment_rate_limit(ip: str) -> bool:
    """Returns True if request is allowed, False if rate limited."""
    now = time.time()
    cutoff = now - COMMENT_RATE_WINDOW
    _comment_attempts[ip] = [t for t in _comment_attempts[ip] if t > cutoff]
    return len(_comment_attempts[ip]) < COMMENT_RATE_LIMIT


def record_comment_attempt(ip: str) -> None:
    _comment_attempts[ip].append(time.time())


async def check_blacklist(session: AsyncSession, text: str) -> str | None:
    """Returns the matched word if found, None if clean."""
    result = await session.execute(select(BlacklistedWord.word))
    words = [row[0] for row in result.all()]

    text_lower = text.lower()
    for word in words:
        if word.lower() in text_lower:
            return word
    return None
