
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.history import History


async def create_history(
    db: AsyncSession,
    history: History,
) -> History:
    db.add(history)
    await db.flush()
    await db.refresh(history)
    return history


async def get_user_history(
    db: AsyncSession,
    user_id: int,
) -> list[History]:
    statement = (
        select(History)
        .where(History.user_id == user_id)
        .options(joinedload(History.news))
        .order_by(History.view_time.desc(), History.id.desc())
    )
    return list((await db.scalars(statement)).unique().all())


async def delete_history(
    db: AsyncSession,
    user_id: int,
    history_id: int,
) -> bool:
    statement = delete(History).where(
        History.id == history_id,
        History.user_id == user_id,
    )
    result = await db.execute(statement)
    return result.rowcount > 0


async def clear_user_history(
    db: AsyncSession,
    user_id: int,
) -> int:
    statement = delete(History).where(History.user_id == user_id)
    result = await db.execute(statement)
    return int(result.rowcount or 0)
