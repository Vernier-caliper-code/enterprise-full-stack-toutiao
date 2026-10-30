
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.users import User, UserToken


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(User, user_id)


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    statement = select(User).where(User.username == username)
    return await db.scalar(statement)


async def get_user_by_token(db: AsyncSession, token: str) -> User | None:
    statement = (
        select(User)
        .join(UserToken)
        .where(
            UserToken.token == token,
            UserToken.expires_at > func.now(),
        )
    )
    return await db.scalar(statement)


async def create_user(db: AsyncSession, user: User) -> User:
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def create_user_token(
    db: AsyncSession,
    user_id: int,
    token: str,
    expires_at: datetime,
) -> UserToken:
    user_token = UserToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
    )
    db.add(user_token)
    await db.flush()
    return user_token


async def update_user(
    db: AsyncSession,
    user: User,
    values: dict[str, Any],
) -> User:
    for field, value in values.items():
        setattr(user, field, value)
    await db.flush()
    await db.refresh(user)
    return user


async def update_user_password(
    db: AsyncSession,
    user: User,
    password_hash: str,
) -> None:
    user.password = password_hash
    await db.flush()
