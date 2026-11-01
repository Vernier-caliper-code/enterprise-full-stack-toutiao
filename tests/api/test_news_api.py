import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.api


async def test_get_categories_returns_sorted_camel_case_data(
    app_client: AsyncClient,
    catalog: dict,
) -> None:
    # Act
    response = await app_client.get("/api/news/categories")

    # Assert
    assert response.status_code == 200
    data = response.json()["data"]
    assert [item["name"] for item in data] == ["科技", "体育"]
    assert [item["sortOrder"] for item in data] == [1, 2]


async def test_get_news_list_filters_paginates_and_reports_more(
    app_client: AsyncClient,
    catalog: dict,
) -> None:
    # Arrange
    category_id = catalog["categories"][0].id

    # Act
    response = await app_client.get(
        "/api/news/list",
        params={"categoryId": category_id, "page": 1, "pageSize": 1},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2
    assert data["hasMore"] is True
    assert [item["id"] for item in data["list"]] == [catalog["latest"].id]


async def test_get_news_detail_increments_views_and_returns_related_news(
    app_client: AsyncClient,
    catalog: dict,
) -> None:
    # Arrange
    latest = catalog["latest"]
    original_views = latest.views

    # Act
    response = await app_client.get(
        "/api/news/detail",
        params={"id": latest.id},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == latest.id
    assert data["views"] == original_views + 1
    assert data["categoryId"] == latest.category_id
    assert [item["id"] for item in data["relatedNews"]] == [catalog["older"].id]
