import secrets
from datetime import UTC, datetime, timedelta

from passlib.context import CryptContext

TOKEN_EXPIRE_DAYS = 7

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def generate_token() -> str:
    return secrets.token_urlsafe(48)


def token_expires_at() -> datetime:
    now = datetime.now(UTC).replace(tzinfo=None)
    return now + timedelta(days=TOKEN_EXPIRE_DAYS)
