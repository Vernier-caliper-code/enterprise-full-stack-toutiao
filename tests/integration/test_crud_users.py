from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from toutiao_backend.crud.users import (
    create_user,
    create_user_token,
    get_user_by_id,
    get_user_by_token,
    get_user_by_username,
    update_user,
    update_user_password,
)
from toutiao_backend.models.users import User
from toutiao_backend.utils.security import hash_password, verify_password

pytestmark = pytest.mark.integration


async def test_create_and_query_user(db_session: AsyncSession) -> None:
    # Arrange
    user = User(
        username="CRUD_USER",
        password=hash_password("secret"),
        gender="unknown",
    )

    # Act
    created = await create_user(db_session, user)
    by_id = await get_user_by_id(db_session, created.id)
    by_username = await get_user_by_username(db_session, "CRUD_USER")

    # Assert
    assert created.id > 0
    assert by_id is not None
    assert by_id.username == "CRUD_USER"
    assert by_username is not None
    assert by_username.id == created.id


async def test_create_user_token_and_find_active_user(
    db_session: AsyncSession,
) -> None:
    # Arrange
    user = await create_user(
        db_session,
        User(
            username="TOKEN_USER",
            password=hash_password("secret"),
            gender="unknown",
        ),
    )
    token = await create_user_token(
        db_session,
        user.id,
        "active-token",
        datetime.now(UTC).replace(tzinfo=None) + timedelta(days=1),
    )

    # Act
    found = await get_user_by_token(db_session, token.token)

    # Assert
    assert found is not None
    assert found.id == user.id


async def test_expired_token_is_rejected(db_session: AsyncSession) -> None:
    # Arrange
    user = await create_user(
        db_session,
        User(
            username="EXPIRED_TOKEN_USER",
            password=hash_password("secret"),
            gender="unknown",
        ),
    )
    await create_user_token(
        db_session,
        user.id,
        "expired-token",
        datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1),
    )

    # Act
    found = await get_user_by_token(db_session, "expired-token")

    # Assert
    assert found is None


async def test_update_user_profile_and_password(
    db_session: AsyncSession,
) -> None:
    # Arrange
    user = await create_user(
        db_session,
        User(
            username="UPDATE_USER",
            password=hash_password("old-password"),
            gender="unknown",
        ),
    )

    # Act
    updated = await update_user(
        db_session,
        user,
        {"nickname": "新昵称", "bio": "新简介", "gender": "female"},
    )
    await update_user_password(
        db_session,
        updated,
        hash_password("new-password"),
    )
    await db_session.refresh(updated)

    # Assert
    assert updated.nickname == "新昵称"
    assert updated.bio == "新简介"
    assert updated.gender == "female"
    assert verify_password("new-password", updated.password) is True
    assert verify_password("old-password", updated.password) is False


async def test_unique_username_is_enforced_by_mysql(
    db_session: AsyncSession,
) -> None:
    # Arrange
    db_session.add(
        User(
            username="DUPLICATE_USER",
            password=hash_password("secret"),
            gender="unknown",
        )
    )
    await db_session.flush()

    # Act / Assert
    with pytest.raises(IntegrityError):
        await create_user(
            db_session,
            User(
                username="DUPLICATE_USER",
                password=hash_password("secret"),
                gender="unknown",
            ),
        )
    await db_session.rollback()


async def test_database_is_empty_after_previous_test(
    db_session: AsyncSession,
) -> None:
    # Arrange / Act
    result = await db_session.scalars(select(User))

    # Assert
    assert result.all() == []
