from __future__ import annotations

from collections.abc import AsyncIterator, Iterable
from datetime import datetime, timedelta

from redis.asyncio import Redis
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from .config import (
    CATEGORY_COUNT,
    FAVORITE_COUNT,
    HISTORY_COUNT,
    HOT_HISTORY_COUNT,
    HOT_USER_ID,
    NEWS_COUNT,
    PERFORMANCE_PASSWORD,
    TEST_DATABASE,
    TEST_REDIS_DB,
    TOKEN_PREFIX,
    USER_COUNT,
    configure_test_environment,
    performance_token,
)

configure_test_environment()

from toutiao_backend.config.cache_conf import REDIS_DB, redis_client  # noqa: E402
from toutiao_backend.config.db_conf import DATABASE_URL, Base, engine  # noqa: E402
from toutiao_backend.models.favorite import Favorite  # noqa: E402
from toutiao_backend.models.history import History  # noqa: E402
from toutiao_backend.models.news import News, NewsCategory, RelatedNews  # noqa: E402
from toutiao_backend.models.users import User, UserToken  # noqa: E402
from toutiao_backend.utils.security import hash_password  # noqa: E402

BASE_TIME = datetime(2026, 1, 1, 0, 0, 0)
TOKEN_EXPIRES_AT = datetime(2037, 12, 31, 23, 59, 59)
CATEGORY_NAMES = ("科技", "体育", "财经", "娱乐", "汽车", "教育", "健康", "军事")
CHUNK_SIZE = 1_000


def ensure_safe_targets() -> None:
    if DATABASE_URL.database != TEST_DATABASE:
        raise RuntimeError(
            f"Refusing non-functional tests: database must be {TEST_DATABASE}, "
            f"got {DATABASE_URL.database!r}."
        )

    client_db = redis_client.connection_pool.connection_kwargs.get("db")
    if REDIS_DB != TEST_REDIS_DB or client_db != TEST_REDIS_DB:
        raise RuntimeError(
            "Refusing non-functional tests: Redis DB must be "
            f"{TEST_REDIS_DB}, got REDIS_DB={REDIS_DB!r}, "
            f"client_db={client_db!r}."
        )


def _server_engine() -> AsyncEngine:
    server_url = DATABASE_URL.set(database=None)
    return create_async_engine(server_url, poolclass=NullPool)


def _fresh_redis() -> Redis:
    kwargs = dict(redis_client.connection_pool.connection_kwargs)
    return Redis(
        host=kwargs["host"],
        port=kwargs["port"],
        db=kwargs["db"],
        username=kwargs.get("username"),
        password=kwargs.get("password"),
        decode_responses=True,
        protocol=2,
        socket_connect_timeout=3,
        socket_timeout=3,
    )


async def _create_database_if_missing() -> None:
    admin_engine = _server_engine()
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


async def _flush_redis() -> None:
    fresh = _fresh_redis()
    try:
        actual_db = fresh.connection_pool.connection_kwargs.get("db")
        if actual_db != TEST_REDIS_DB:
            raise RuntimeError(f"Refusing Redis flush for DB {actual_db!r}.")
        await fresh.flushdb()
    finally:
        await fresh.aclose()


async def reset_database() -> None:
    ensure_safe_targets()
    await _create_database_if_missing()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    await _flush_redis()


def _chunks(rows: Iterable[dict], size: int = CHUNK_SIZE):
    chunk: list[dict] = []
    for row in rows:
        chunk.append(row)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


async def _insert_rows(connection, table, rows: Iterable[dict]) -> int:
    inserted = 0
    for chunk in _chunks(rows):
        await connection.execute(table.insert(), chunk)
        inserted += len(chunk)
    return inserted


def _user_rows(password_hash: str) -> Iterable[dict]:
    for user_id in range(1, USER_COUNT + 1):
        created_at = BASE_TIME + timedelta(seconds=user_id)
        yield {
            "id": user_id,
            "username": f"perf_user_{user_id:02d}",
            "password": password_hash,
            "nickname": f"性能测试用户{user_id:02d}",
            "avatar": None,
            "gender": "unknown",
            "bio": "非功能测试固定数据",
            "phone": None,
            "created_at": created_at,
            "updated_at": created_at,
        }


def _token_rows() -> Iterable[dict]:
    for user_id in range(1, USER_COUNT + 1):
        yield {
            "id": user_id,
            "user_id": user_id,
            "token": performance_token(user_id),
            "expires_at": TOKEN_EXPIRES_AT,
            "created_at": BASE_TIME + timedelta(seconds=user_id),
        }


def _category_rows() -> Iterable[dict]:
    for category_id, name in enumerate(CATEGORY_NAMES, start=1):
        yield {
            "id": category_id,
            "name": name,
            "sort_order": category_id,
            "created_at": BASE_TIME,
            "updated_at": BASE_TIME,
        }


def _news_rows() -> Iterable[dict]:
    content_suffix = "非功能测试正文。" * 110
    for news_id in range(1, NEWS_COUNT + 1):
        publish_time = BASE_TIME + timedelta(minutes=news_id)
        yield {
            "id": news_id,
            "title": f"性能基线新闻 {news_id:05d}",
            "description": f"用于性能、并发和慢查询验证的固定新闻 {news_id:05d}",
            "content": f"第 {news_id} 条新闻。{content_suffix}",
            "image": None,
            "author": f"作者{news_id % 97:02d}",
            "category_id": ((news_id - 1) % CATEGORY_COUNT) + 1,
            "views": news_id % 1_000,
            "publish_time": publish_time,
            "created_at": publish_time,
            "updated_at": publish_time,
        }


def _related_news_rows() -> Iterable[dict]:
    related_id = 1
    for news_id in range(1, NEWS_COUNT + 1):
        for offset in range(1, 4):
            target_id = ((news_id + offset - 1) % NEWS_COUNT) + 1
            yield {
                "id": related_id,
                "news_id": news_id,
                "related_news_id": target_id,
                "created_at": BASE_TIME + timedelta(seconds=related_id),
            }
            related_id += 1


def _favorite_rows() -> Iterable[dict]:
    favorite_id = 1
    for user_id in range(1, USER_COUNT + 1):
        for news_id in range(1, 401):
            yield {
                "id": favorite_id,
                "user_id": user_id,
                "news_id": news_id,
                "created_at": BASE_TIME + timedelta(seconds=favorite_id),
            }
            favorite_id += 1


def _history_rows() -> Iterable[dict]:
    history_id = 1

    for news_id in range(1, HOT_HISTORY_COUNT + 1):
        yield {
            "id": history_id,
            "user_id": HOT_USER_ID,
            "news_id": news_id,
            "view_time": BASE_TIME + timedelta(seconds=history_id),
        }
        history_id += 1

    for user_id in range(2, 42):
        for offset in range(1_000):
            yield {
                "id": history_id,
                "user_id": user_id,
                "news_id": (offset % NEWS_COUNT) + 1,
                "view_time": BASE_TIME + timedelta(seconds=history_id),
            }
            history_id += 1


async def seed_database() -> dict[str, int]:
    ensure_safe_targets()
    password_hash = hash_password(PERFORMANCE_PASSWORD)

    async with engine.begin() as connection:
        counts = {}
        counts["user"] = await _insert_rows(
            connection, User.__table__, _user_rows(password_hash)
        )
        counts["user_token"] = await _insert_rows(
            connection, UserToken.__table__, _token_rows()
        )
        counts["news_category"] = await _insert_rows(
            connection, NewsCategory.__table__, _category_rows()
        )
        counts["news"] = await _insert_rows(connection, News.__table__, _news_rows())
        counts["related_news"] = await _insert_rows(
            connection, RelatedNews.__table__, _related_news_rows()
        )
        counts["favorite"] = await _insert_rows(
            connection, Favorite.__table__, _favorite_rows()
        )
        counts["history"] = await _insert_rows(
            connection, History.__table__, _history_rows()
        )

    expected = {
        "user": USER_COUNT,
        "user_token": USER_COUNT,
        "news_category": CATEGORY_COUNT,
        "news": NEWS_COUNT,
        "related_news": NEWS_COUNT * 3,
        "favorite": FAVORITE_COUNT,
        "history": HISTORY_COUNT,
    }
    if counts != expected:
        raise RuntimeError(f"Seeded row counts differ from contract: {counts!r}")

    return counts


async def database_counts() -> dict[str, int]:
    ensure_safe_targets()
    tables = {
        "user": User,
        "user_token": UserToken,
        "news_category": NewsCategory,
        "news": News,
        "related_news": RelatedNews,
        "favorite": Favorite,
        "history": History,
    }
    async with engine.connect() as connection:
        counts = {}
        for name, model in tables.items():
            statement = select(func.count()).select_from(model)
            counts[name] = int(await connection.scalar(statement) or 0)
    return counts


async def verify_seed() -> dict[str, int]:
    counts = await database_counts()
    expected = {
        "user": USER_COUNT,
        "user_token": USER_COUNT,
        "news_category": CATEGORY_COUNT,
        "news": NEWS_COUNT,
        "related_news": NEWS_COUNT * 3,
        "favorite": FAVORITE_COUNT,
        "history": HISTORY_COUNT,
    }
    if counts != expected:
        raise RuntimeError(
            "Non-functional data is not ready. Run "
            "`python -m nonfunctional.seed`. "
            f"Expected {expected!r}, got {counts!r}."
        )
    return counts


async def prepare_and_seed() -> dict[str, int]:
    await reset_database()
    counts = await seed_database()
    await verify_seed()
    return counts


async def cleanup_database(*, dispose_global_engine: bool = True) -> None:
    ensure_safe_targets()
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
    finally:
        if dispose_global_engine:
            await engine.dispose()
    await _flush_redis()


def hot_user_token() -> str:
    return performance_token(HOT_USER_ID)


def token_for_user(user_id: int) -> str:
    if not 1 <= user_id <= USER_COUNT:
        raise ValueError(f"user_id must be between 1 and {USER_COUNT}")
    return performance_token(user_id)
