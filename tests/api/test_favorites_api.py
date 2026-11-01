from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toutiao_backend.models.favorite import Favorite

pytestmark = pytest.mark.api


async def _create_favorite(
    db_session: AsyncSession,
    user_id: int,
    news_id: int,
    created_at: datetime | None = None,
) -> Favorite:
    values = {"user_id": user_id, "news_id": news_id}
    if created_at is not None:
        values["created_at"] = created_at
    favorite = Favorite(**values)
    db_session.add(favorite)
    await db_session.flush()
    await db_session.refresh(favorite)
    return favorite


async def test_check_favorite_requires_auth_and_reports_current_state(
    app_client: AsyncClient,
    db_session: AsyncSession,
    user_with_token: dict,
    catalog: dict,
) -> None:
    # Arrange
    user_id = user_with_token["user"].id
    news_id = catalog["latest"].id

    # Act
    unauthorized = await app_client.get(
        "/api/favorite/check",
        params={"newsId": news_id},
    )
    before = await app_client.get(
        "/api/favorite/check",
        params={"newsId": news_id},
        headers=user_with_token["headers"],
    )
    await _create_favorite(db_session, user_id, news_id)
    after = await app_client.get(
        "/api/favorite/check",
        params={"newsId": news_id},
        headers=user_with_token["headers"],
    )

    # Assert
    assert unauthorized.status_code == 401
    assert before.status_code == 200
    assert before.json()["data"]["isFavorite"] is False
    assert after.status_code == 200
    assert after.json()["data"]["isFavorite"] is True


async def test_add_favorite_is_idempotent(
    app_client: AsyncClient,
    db_session: AsyncSession,
    user_with_token: dict,
    catalog: dict,
) -> None:
    # Arrange
    news_id = catalog["latest"].id
    payload = {"newsId": news_id}

    # Act
    first = await app_client.post(
        "/api/favorite/add",
        json=payload,
        headers=user_with_token["headers"],
    )
    second = await app_client.post(
        "/api/favorite/add",
        json=payload,
        headers=user_with_token["headers"],
    )
    stored = await db_session.scalar(
        select(Favorite).where(
            Favorite.user_id == user_with_token["user"].id,
            Favorite.news_id == news_id,
        )
    )

    # Assert
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["message"] == "收藏成功"
    assert first.json()["data"]["userId"] == user_with_token["user"].id
    assert first.json()["data"]["newsId"] == news_id
    assert second.json()["data"]["id"] == first.json()["data"]["id"]
    assert stored is not None


async def test_remove_favorite_deletes_only_requested_news(
    app_client: AsyncClient,
    db_session: AsyncSession,
    user_with_token: dict,
    catalog: dict,
) -> None:
    # Arrange
    user_id = user_with_token["user"].id
    news_id = catalog["latest"].id
    await _create_favorite(db_session, user_id, news_id)

    # Act
    response = await app_client.delete(
        "/api/favorite/remove",
        params={"newsId": news_id},
        headers=user_with_token["headers"],
    )
    stored = await db_session.scalar(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.news_id == news_id,
        )
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == "取消收藏成功"
    assert stored is None


async def test_favorite_list_paginates_and_uses_camel_case(
    app_client: AsyncClient,
    db_session: AsyncSession,
    user_with_token: dict,
    catalog: dict,
) -> None:
    # Arrange
    user_id = user_with_token["user"].id
    first = await _create_favorite(
        db_session,
        user_id,
        catalog["older"].id,
        datetime(2026, 1, 1, 8, 0, 0),
    )
    second = await _create_favorite(
        db_session,
        user_id,
        catalog["latest"].id,
        datetime(2026, 1, 2, 8, 0, 0),
    )

    # Act
    response = await app_client.get(
        "/api/favorite/list",
        params={"page": 1, "pageSize": 1},
        headers=user_with_token["headers"],
    )

    # Assert
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2
    assert data["hasMore"] is True
    assert data["list"][0]["id"] == second.id
    assert data["list"][0]["favoriteTime"]
    assert first.id != second.id


async def test_clear_favorites_removes_all_owned_records(
    app_client: AsyncClient,
    db_session: AsyncSession,
    user_with_token: dict,
    catalog: dict,
) -> None:
    # Arrange
    user_id = user_with_token["user"].id
    await _create_favorite(db_session, user_id, catalog["latest"].id)
    await _create_favorite(db_session, user_id, catalog["older"].id)

    # Act
    response = await app_client.delete(
        "/api/favorite/clear",
        headers=user_with_token["headers"],
    )
    remaining = await db_session.scalars(
        select(Favorite).where(Favorite.user_id == user_id)
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == "成功删除2条收藏记录"
    assert remaining.all() == []
