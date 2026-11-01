import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toutiao_backend.crud.news import (
    count_news_by_category,
    get_news_categories,
    get_news_detail,
    get_news_list,
    get_related_news,
    increment_news_views,
)
from toutiao_backend.models.news import News

pytestmark = pytest.mark.integration


async def test_categories_are_sorted_by_sort_order(
    db_session: AsyncSession,
    catalog: dict,
) -> None:
    # Arrange
    expected_ids = [category.id for category in catalog["categories"]]

    # Act
    categories = await get_news_categories(db_session)

    # Assert
    assert [category.id for category in categories] == expected_ids
    assert [category.name for category in categories] == ["科技", "体育"]


async def test_news_list_filters_and_paginates(
    db_session: AsyncSession,
    catalog: dict,
) -> None:
    # Arrange
    technology = catalog["categories"][0]

    # Act
    first_page = await get_news_list(
        db_session,
        technology.id,
        offset=0,
        limit=1,
    )
    second_page = await get_news_list(
        db_session,
        technology.id,
        offset=1,
        limit=1,
    )
    total = await count_news_by_category(db_session, technology.id)

    # Assert
    assert [item.id for item in first_page] == [catalog["latest"].id]
    assert [item.id for item in second_page] == [catalog["older"].id]
    assert total == 2
    assert all(item.category_id == technology.id for item in first_page)


async def test_related_news_uses_relation_table(
    db_session: AsyncSession,
    catalog: dict,
) -> None:
    # Arrange
    latest = catalog["latest"]

    # Act
    related = await get_related_news(db_session, latest.id)

    # Assert
    assert [item.id for item in related] == [catalog["older"].id]


async def test_increment_news_views_commits_new_value(
    db_session: AsyncSession,
    catalog: dict,
) -> None:
    # Arrange
    latest = catalog["latest"]
    original_views = latest.views

    # Act
    new_views = await increment_news_views(db_session, latest.id)
    detail = await get_news_detail(db_session, latest.id)

    # Assert
    assert new_views == original_views + 1
    assert detail is not None
    assert detail.views == original_views + 1


async def test_increment_unknown_news_returns_none(
    db_session: AsyncSession,
) -> None:
    # Arrange
    missing_id = 999_999

    # Act
    result = await increment_news_views(db_session, missing_id)

    # Assert
    assert result is None


async def test_news_rows_roll_back_between_tests(
    db_session: AsyncSession,
) -> None:
    # Arrange / Act
    result = await db_session.scalars(select(News))

    # Assert
    assert result.all() == []
