from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import delete, select

from nonfunctional.dataset import token_for_user
from toutiao_backend.config.db_conf import AsyncSessionLocal
from toutiao_backend.models.favorite import Favorite
from toutiao_backend.models.news import News

pytestmark = [pytest.mark.nonfunctional]


async def _news_views(news_id: int) -> int:
    async with AsyncSessionLocal() as session:
        value = await session.scalar(select(News.views).where(News.id == news_id))
        return int(value or 0)


async def delete_favorite_row(session, user_id: int, news_id: int) -> None:
    await session.execute(
        delete(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.news_id == news_id,
        )
    )
    await session.commit()


async def _favorite_exists(user_id: int, news_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        value = await session.scalar(
            select(Favorite.id).where(
                Favorite.user_id == user_id,
                Favorite.news_id == news_id,
            )
        )
        return value is not None


@pytest.mark.xfail(
    strict=False,
    reason="Duplicate favorite races raise MissingGreenlet after rollback.",
)
async def test_concurrent_duplicate_favorite_is_idempotent(
    api_client,
    db_session,
) -> None:
    user_id = 50
    news_id = 9_999
    headers = {"Authorization": token_for_user(user_id)}

    await delete_favorite_row(db_session, user_id, news_id)
    try:
        responses = await asyncio.gather(
            *(
                api_client.post(
                    "/api/favorite/add",
                    headers=headers,
                    json={"newsId": news_id},
                )
                for _ in range(20)
            )
        )
    except Exception as exc:
        raise AssertionError(
            f"Concurrent favorite request failed with {type(exc).__name__}: {exc}"
        ) from exc

    statuses = [response.status_code for response in responses]
    codes = [response.json()["code"] for response in responses]
    assert all(response.status_code == 200 for response in responses), (
        f"Concurrent favorite statuses: {statuses}; codes: {codes}"
    )
    assert all(response.json()["code"] == 200 for response in responses)
    assert await _favorite_exists(user_id, news_id)


async def test_concurrent_login_returns_distinct_tokens(api_client) -> None:
    responses = await asyncio.gather(
        *(
            api_client.post(
                "/api/user/login",
                json={
                    "username": "perf_user_01",
                    "password": "performance-password",
                },
            )
            for _ in range(20)
        )
    )

    assert all(response.status_code == 200 for response in responses)
    tokens = {response.json()["data"]["token"] for response in responses}
    assert len(tokens) == 20


async def test_history_isolated_between_concurrent_users(api_client) -> None:
    user_a_id, news_a_id = 2, 9_900
    user_b_id, news_b_id = 3, 9_901
    headers_a = {"Authorization": token_for_user(user_a_id)}
    headers_b = {"Authorization": token_for_user(user_b_id)}

    response_a, response_b = await asyncio.gather(
        api_client.post(
            "/api/history/add",
            headers=headers_a,
            json={"newsId": news_a_id},
        ),
        api_client.post(
            "/api/history/add",
            headers=headers_b,
            json={"newsId": news_b_id},
        ),
    )
    assert response_a.status_code == 200
    assert response_b.status_code == 200

    list_a, list_b = await asyncio.gather(
        api_client.get("/api/history/list", headers=headers_a),
        api_client.get("/api/history/list", headers=headers_b),
    )
    assert list_a.status_code == 200
    assert list_b.status_code == 200
    assert list_a.json()["data"]["list"][0]["newsId"] == news_a_id
    assert list_b.json()["data"]["list"][0]["newsId"] == news_b_id


