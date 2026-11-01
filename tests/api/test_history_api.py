from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toutiao_backend.models.history import History

pytestmark = pytest.mark.api


async def _create_history(
    db_session: AsyncSession,
    user_id: int,
    news_id: int,
    view_time: datetime | None = None,
) -> History:
    values = {"user_id": user_id, "news_id": news_id}
    if view_time is not None:
        values["view_time"] = view_time
    history = History(**values)
    db_session.add(history)
    await db_session.flush()
    await db_session.refresh(history)
    return history


async def test_add_history_invalidates_cached_list(
    app_client: AsyncClient,
    user_with_token: dict,
    catalog: dict,
) -> None:
    # Arrange
    headers = user_with_token["headers"]
    empty = await app_client.get("/api/history/list", headers=headers)

    # Act
    response = await app_client.post(
        "/api/history/add",
        json={"newsId": catalog["latest"].id},
        headers=headers,
    )
    refreshed = await app_client.get("/api/history/list", headers=headers)

    # Assert
    assert empty.status_code == 200
    assert empty.json()["data"]["total"] == 0
    assert response.status_code == 200
    assert response.json()["message"] == "添加成功"
    assert response.json()["data"]["newsId"] == catalog["latest"].id
    assert refreshed.json()["data"]["total"] == 1


async def test_history_list_paginates_in_reverse_chronological_order(
    app_client: AsyncClient,
    db_session: AsyncSession,
    user_with_token: dict,
    catalog: dict,
) -> None:
    # Arrange
    user_id = user_with_token["user"].id
    oldest = await _create_history(
        db_session,
        user_id,
        catalog["sports_news"].id,
        datetime(2026, 1, 1, 8, 0, 0),
    )
    middle = await _create_history(
        db_session,
        user_id,
        catalog["older"].id,
        datetime(2026, 1, 2, 8, 0, 0),
    )
    newest = await _create_history(
        db_session,
        user_id,
        catalog["latest"].id,
        datetime(2026, 1, 3, 8, 0, 0),
    )

    # Act
    response = await app_client.get(
        "/api/history/list",
        params={"page": 1, "pageSize": 2},
        headers=user_with_token["headers"],
    )

    # Assert
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 3
    assert data["hasMore"] is True
    assert [item["id"] for item in data["list"]] == [newest.id, middle.id]
    assert data["list"][0]["viewTime"]
    assert oldest.id not in [item["id"] for item in data["list"]]


async def test_delete_history_returns_404_after_record_is_gone(
    app_client: AsyncClient,
    db_session: AsyncSession,
    user_with_token: dict,
    catalog: dict,
) -> None:
    # Arrange
    history = await _create_history(
        db_session,
        user_with_token["user"].id,
        catalog["latest"].id,
    )
    headers = user_with_token["headers"]

    # Act
    response = await app_client.delete(
        f"/api/history/delete/{history.id}",
        headers=headers,
    )
    repeated = await app_client.delete(
        f"/api/history/delete/{history.id}",
        headers=headers,
    )
    stored = await db_session.scalar(
        select(History).where(History.id == history.id)
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == "删除成功"
    assert repeated.status_code == 404
    assert repeated.json()["message"] == "浏览记录不存在"
    assert stored is None


async def test_clear_history_removes_all_owned_records(
    app_client: AsyncClient,
    db_session: AsyncSession,
    user_with_token: dict,
    catalog: dict,
) -> None:
    # Arrange
    user_id = user_with_token["user"].id
    await _create_history(db_session, user_id, catalog["latest"].id)
    await _create_history(db_session, user_id, catalog["older"].id)

    # Act
    response = await app_client.delete(
        "/api/history/clear",
        headers=user_with_token["headers"],
    )
    remaining = await db_session.scalars(
        select(History).where(History.user_id == user_id)
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == "清空成功"
    assert remaining.all() == []
