import os
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_DATABASE = "news_app_test"
TEST_REDIS_DB = 15

load_dotenv(PROJECT_ROOT / ".env.test.local")
os.environ["MYSQL_DATABASE"] = TEST_DATABASE
os.environ["REDIS_DB"] = str(TEST_REDIS_DB)

from toutiao_backend.config.cache_conf import REDIS_DB, redis_client
from toutiao_backend.config.db_conf import DATABASE_URL, Base, engine, get_db
from toutiao_backend.main import app
from toutiao_backend.models import News, NewsCategory, RelatedNews, User
from toutiao_backend.models.users import UserToken
from toutiao_backend.utils.security import hash_password, token_expires_at


def _assert_safe_test_targets() -> None:
    if DATABASE_URL.database != TEST_DATABASE:
        raise RuntimeError(
            f"Refusing to run: database must be {TEST_DATABASE}, "
            f"got {DATABASE_URL.database!r}."
        )

    redis_db = redis_client.connection_pool.connection_kwargs.get("db")
    if REDIS_DB != TEST_REDIS_DB or redis_db != TEST_REDIS_DB:
        raise RuntimeError(
            f"Refusing to run: Redis DB must be {TEST_REDIS_DB}, "
            f"got REDIS_DB={REDIS_DB!r}, client_db={redis_db!r}."
        )


def _server_url_without_database() -> URL:
    return URL.create(
        drivername=DATABASE_URL.drivername,
        username=DATABASE_URL.username,
        password=DATABASE_URL.password,
        host=DATABASE_URL.host,
        port=DATABASE_URL.port,
        query=DATABASE_URL.query,
    )


async def _create_database() -> None:
    admin_engine: AsyncEngine = create_async_engine(
        _server_url_without_database(),
        poolclass=NullPool,
    )
    try:
        async with admin_engine.begin() as connection:
            await connection.execute(
                text(
                    "CREATE DATABASE IF NOT EXISTS news_app_test "
                    "DEFAULT CHARACTER SET utf8mb4 "
                    "COLLATE utf8mb4_unicode_ci"
                )
            )
    finally:
        await admin_engine.dispose()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def prepared_test_database() -> AsyncIterator[None]:
    _assert_safe_test_targets()

    try:
        await _create_database()
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)
        await redis_client.flushdb()
    except Exception as exc:
        raise RuntimeError(
            "Cannot prepare the isolated test environment. "
            "Configure MySQL credentials in .env.test.local and ensure "
            "the account can manage news_app_test."
        ) from exc

    try:
        yield
    finally:
        await redis_client.flushdb()
        await redis_client.aclose()
        await engine.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def db_session(
    prepared_test_database: None,
) -> AsyncIterator[AsyncSession]:
    del prepared_test_database

    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest_asyncio.fixture(loop_scope="session")
async def clean_redis(
    prepared_test_database: None,
) -> AsyncIterator[Any]:
    del prepared_test_database
    _assert_safe_test_targets()
    await redis_client.flushdb()

    try:
        yield redis_client
    finally:
        await redis_client.flushdb()


@pytest_asyncio.fixture(loop_scope="session")
async def app_client(
    db_session: AsyncSession,
    clean_redis: Any,
) -> AsyncIterator[AsyncClient]:
    del clean_redis

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(loop_scope="session")
async def catalog(db_session: AsyncSession) -> dict[str, Any]:
    technology = NewsCategory(name="科技", sort_order=1)
    sports = NewsCategory(name="体育", sort_order=2)
    db_session.add_all([technology, sports])
    await db_session.flush()

    latest = News(
        title="最新科技新闻",
        description="第一篇测试新闻",
        content="新闻正文一",
        author="作者甲",
        category_id=technology.id,
        views=10,
        publish_time=datetime(2026, 1, 3, 8, 0, 0),
    )
    older = News(
        title="较早科技新闻",
        description="第二篇测试新闻",
        content="新闻正文二",
        author="作者乙",
        category_id=technology.id,
        views=20,
        publish_time=datetime(2026, 1, 2, 8, 0, 0),
    )
    sports_news = News(
        title="体育新闻",
        description="体育测试新闻",
        content="新闻正文三",
        author="作者丙",
        category_id=sports.id,
        views=30,
        publish_time=datetime(2026, 1, 1, 8, 0, 0),
    )
    db_session.add_all([latest, older, sports_news])
    await db_session.flush()

    db_session.add(
        RelatedNews(
            news_id=latest.id,
            related_news_id=older.id,
        )
    )
    await db_session.flush()

    return {
        "categories": [technology, sports],
        "news": [latest, older, sports_news],
        "latest": latest,
        "older": older,
        "sports_news": sports_news,
    }


@pytest_asyncio.fixture(loop_scope="session")
async def user_with_token(db_session: AsyncSession) -> dict[str, Any]:
    user = User(
        username="TEST_USER",
        password=hash_password("test-password"),
        gender="unknown",
        avatar="https://example.com/avatar.png",
        bio="integration test user",
    )
    db_session.add(user)
    await db_session.flush()

    token = "test-token"
    db_session.add(
        UserToken(
            user_id=user.id,
            token=token,
            expires_at=token_expires_at(),
        )
    )
    await db_session.flush()

    return {
        "user": user,
        "token": token,
        "headers": {"Authorization": token},
    }
