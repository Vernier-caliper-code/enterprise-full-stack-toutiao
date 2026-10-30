from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.news import News, NewsCategory, RelatedNews


async def get_news_categories(db: AsyncSession) -> list[NewsCategory]:
    statement = select(NewsCategory).order_by(
        NewsCategory.sort_order.asc(),
        NewsCategory.id.asc(),
    )
    return list((await db.scalars(statement)).all())


async def get_news_category_by_id(
    db: AsyncSession,
    category_id: int,
) -> NewsCategory | None:
    return await db.get(NewsCategory, category_id)


async def get_news_list(
    db: AsyncSession,
    category_id: int,
    offset: int,
    limit: int,
) -> list[News]:
    statement = (
        select(News)
        .where(News.category_id == category_id)
        .options(selectinload(News.category))
        .order_by(News.publish_time.desc(), News.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list((await db.scalars(statement)).all())


async def count_news_by_category(
    db: AsyncSession,
    category_id: int,
) -> int:
    statement = (
        select(func.count()).select_from(News).where(News.category_id == category_id)
    )
    return int(await db.scalar(statement) or 0)


async def get_news_detail(
    db: AsyncSession,
    news_id: int,
) -> News | None:
    return await db.get(News, news_id)


async def get_related_news(
    db: AsyncSession,
    news_id: int,
) -> list[News]:
    statement = (
        select(News)
        .join(
            RelatedNews,
            RelatedNews.related_news_id == News.id,
        )
        .where(RelatedNews.news_id == news_id)
        .options(selectinload(News.category))
        .order_by(News.publish_time.desc(), News.id.desc())
    )
    return list((await db.scalars(statement)).all())


async def increment_news_views(
    db: AsyncSession,
    news_id: int,
) -> int | None:
    result = await db.execute(
        update(News).where(News.id == news_id).values(views=News.views + 1)
    )
    if result.rowcount == 0:
        await db.rollback()
        return None

    await db.commit()
    statement = select(News.views).where(News.id == news_id)
    return int(await db.scalar(statement) or 0)
