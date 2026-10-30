from datetime import UTC, datetime, timedelta

from toutiao_backend.utils.security import (
    TOKEN_EXPIRE_DAYS,
    generate_token,
    hash_password,
    token_expires_at,
    verify_password,
)


def test_password_hash_can_be_verified_without_storing_plaintext() -> None:
    # Arrange
    password = "correct-password"

    # Act
    password_hash = hash_password(password)

    # Assert
    assert password_hash != password
    assert verify_password(password, password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_generated_tokens_are_unique_and_url_safe() -> None:
    # Arrange
    token_count = 20
    allowed_characters = set(
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789-_"
    )

    # Act
    tokens = [generate_token() for _ in range(token_count)]

    # Assert
    assert len(set(tokens)) == token_count
    assert all(set(token) <= allowed_characters for token in tokens)
    assert all(len(token) >= 48 for token in tokens)


def test_token_expiry_is_seven_days_from_now() -> None:
    # Arrange
    before = datetime.now(UTC).replace(tzinfo=None)

    # Act
    expires_at = token_expires_at()

    # Assert
    after = datetime.now(UTC).replace(tzinfo=None)
    assert before + timedelta(days=TOKEN_EXPIRE_DAYS) <= expires_at
    assert expires_at <= after + timedelta(days=TOKEN_EXPIRE_DAYS)
