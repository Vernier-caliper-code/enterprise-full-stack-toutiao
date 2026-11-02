from __future__ import annotations

import time

import httpx
import pytest
from redis.asyncio import Redis
from sqlalchemy import delete, func, select

from nonfunctional.config import TEST_REDIS_DB
from nonfunctional.dataset import token_for_user
from nonfunctional.server_utils import running_server
from toutiao_backend.config.cache_conf import REDIS_DB, REDIS_HOST, REDIS_PORT
from toutiao_backend.config.db_conf import AsyncSessionLocal
from toutiao_backend.models.history import History

pytestmark = [pytest.mark.nonfunctional]


def _redis_client() -> Redis:
    return Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
        protocol=2,
        socket_connect_timeout=3,
        socket_timeout=3,
    )


async def _flush_test_redis() -> None:
    client = _redis_client()
    try:
        actual_db = client.connection_pool.connection_kwargs.get("db")
        assert actual_db == TEST_REDIS_DB
        await client.flushdb()
    finally:
        await client.aclose()


async def test_reads_degrade_when_redis_is_unavailable() -> None:
    with running_server(8121, redis_port=6399, name="redis-unavailable") as server:
        async with httpx.AsyncClient(base_url=server.url, timeout=10) as client:
            started = time.monotonic()
            responses = [
                await client.get("/api/news/categories"),
                await client.get(
                    "/api/news/list",
                    params={"categoryId": 1, "page": 1, "pageSize": 10},
                ),
                await client.get("/api/news/detail", params={"id": 9_000}),
            ]
            elapsed = time.monotonic() - started

    assert [response.status_code for response in responses] == [200, 200, 200]
    assert elapsed < 15


async def test_history_write_survives_cache_invalidation_failure() -> None:
    user_id, news_id = 49, 8_000
    headers = {"Authorization": token_for_user(user_id)}

    async with AsyncSessionLocal() as session:
        before = await session.scalar(
            select(func.count())
            .select_from(History)
            .where(History.user_id == user_id, History.news_id == news_id)
        )

    with running_server(8122, redis_port=6399, name="cache-write-failure") as server:
        async with httpx.AsyncClient(base_url=server.url, timeout=10) as client:
            response = await client.post(
                "/api/history/add",
                headers=headers,
                json={"newsId": news_id},
            )

    async with AsyncSessionLocal() as session:
        after = await session.scalar(
            select(func.count())
            .select_from(History)
            .where(History.user_id == user_id, History.news_id == news_id)
        )

    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(History).where(
                History.user_id == user_id,
                History.news_id == news_id,
            )
        )
        await session.commit()

    assert int(after or 0) == int(before or 0) + 1
    assert response.status_code == 200


async def test_database_outage_returns_503_within_five_seconds() -> None:
    await _flush_test_redis()
    with running_server(
        8123,
        mysql_port=1,
        name="database-unavailable",
    ) as server:
        async with httpx.AsyncClient(base_url=server.url, timeout=10) as client:
            started = time.monotonic()
            response = await client.get(
                "/api/news/list",
                params={"categoryId": 8, "page": 99, "pageSize": 10},
            )
            elapsed = time.monotonic() - started

    assert elapsed < 5
    assert response.status_code == 503


async def test_cache_is_rebuilt_after_recovery(api_client) -> None:
    await _flush_test_redis()
    response = await api_client.get("/api/news/categories")
    assert response.status_code == 200

    redis = _redis_client()
    try:
        assert await redis.exists("news:categories") == 1
    finally:
        await redis.aclose()



