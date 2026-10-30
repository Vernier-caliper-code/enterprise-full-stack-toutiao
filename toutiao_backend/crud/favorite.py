
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.favorite import Favorite


async def get_favorite(
    db: AsyncSession,
    user_id: int,
    news_id: int,
) -> Favorite | None:
    statement = select(Favorite).where(
        Favorite.user_id == user_id,
        Favorite.news_id == news_id,
    )
    return await db.scalar(statement)


async def create_favorite(
    db: AsyncSession,
    favorite: Favorite,
) -> Favorite:
    db.add(favorite)
    await db.flush()
    await db.refresh(favorite)
    return favorite


async def get_user_favorites(
    db: AsyncSession,
    user_id: int,
    offset: int,
    limit: int,
) -> list[Favorite]:
    statement = (
        select(Favorite)
        .where(Favorite.user_id == user_id)
        .options(joinedload(Favorite.news))
        .order_by(Favorite.created_at.desc(), Favorite.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list((await db.scalars(statement)).unique().all())


async def count_user_favorites(
    db: AsyncSession,
    user_id: int,
) -> int:
    statement = (
        select(func.count())
        .select_from(Favorite)
        .where(Favorite.user_id == user_id)
    )
    return int(await db.scalar(statement) or 0)


async def delete_favorite(
    db: AsyncSession,
    user_id: int,
    news_id: int,
) -> bool:
    statement = delete(Favorite).where(
        Favorite.user_id == user_id,
        Favorite.news_id == news_id,
    )
    result = await db.execute(statement)
    return result.rowcount > 0


async def clear_user_favorites(
    db: AsyncSession,
    user_id: int,
) -> int:
    statement = delete(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(statement)
    return int(result.rowcount or 0)
