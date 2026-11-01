import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.e2e


async def test_reader_account_and_news_journey(
    app_client: AsyncClient,
    catalog: dict,
) -> None:
    # Arrange
    username = "E2E_READER"
    password = "reader-password"
    new_password = "reader-new-password"

    # Act: create an account and obtain an authenticated session.
    registration = await app_client.post(
        "/api/user/register",
        json={"username": username, "password": password},
    )
    token = registration.json()["data"]["token"]
    headers = {"Authorization": token}

    # Assert
    assert registration.status_code == 200

    # Act: update the profile and change the password.
    profile = await app_client.put(
        "/api/user/update",
        json={"nickname": "端到端读者", "bio": "正在阅读科技新闻"},
        headers=headers,
    )
    password_change = await app_client.put(
        "/api/user/password",
        json={"oldPassword": password, "newPassword": new_password},
        headers=headers,
    )
    login = await app_client.post(
        "/api/user/login",
        json={"username": username, "password": new_password},
    )
    token = login.json()["data"]["token"]
    headers = {"Authorization": token}

    # Assert
    assert profile.status_code == 200
    assert profile.json()["data"]["nickname"] == "端到端读者"
    assert password_change.status_code == 200
    assert login.status_code == 200

    # Act: browse category, list, and detail.
    categories = await app_client.get("/api/news/categories")
    category_id = catalog["categories"][0].id
    news_list = await app_client.get(
        "/api/news/list",
        params={"categoryId": category_id, "page": 1, "pageSize": 10},
    )
    news_id = catalog["latest"].id
    detail = await app_client.get(
        "/api/news/detail",
        params={"id": news_id},
    )

    # Assert
    assert categories.status_code == 200
    assert news_list.status_code == 200
    assert news_list.json()["data"]["total"] == 2
    assert detail.status_code == 200
    assert detail.json()["data"]["title"] == "最新科技新闻"

    # Act: favorite the news, then add and read browsing history.
    before_favorite = await app_client.get(
        "/api/favorite/check",
        params={"newsId": news_id},
        headers=headers,
    )
    added_favorite = await app_client.post(
        "/api/favorite/add",
        json={"newsId": news_id},
        headers=headers,
    )
    favorites = await app_client.get(
        "/api/favorite/list",
        headers=headers,
    )
    added_history = await app_client.post(
        "/api/history/add",
        json={"newsId": news_id},
        headers=headers,
    )
    history = await app_client.get(
        "/api/history/list",
        headers=headers,
    )

    # Assert
    assert before_favorite.json()["data"]["isFavorite"] is False
    assert added_favorite.status_code == 200
    assert favorites.json()["data"]["total"] == 1
    assert added_history.status_code == 200
    assert history.json()["data"]["total"] == 1
    assert history.json()["data"]["list"][0]["id"] == added_history.json()["data"]["id"]

    # Act: remove favorite and history records.
    removed_favorite = await app_client.delete(
        "/api/favorite/remove",
        params={"newsId": news_id},
        headers=headers,
    )
    cleared_favorites = await app_client.delete(
        "/api/favorite/clear",
        headers=headers,
    )
    history_id = added_history.json()["data"]["id"]
    deleted_history = await app_client.delete(
        f"/api/history/delete/{history_id}",
        headers=headers,
    )
    cleared_history = await app_client.delete(
        "/api/history/clear",
        headers=headers,
    )

    # Assert
    assert removed_favorite.status_code == 200
    assert cleared_favorites.status_code == 200
    assert deleted_history.status_code == 200
    assert cleared_history.status_code == 200
