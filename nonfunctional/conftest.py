from __future__ import annotations

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from .config import configure_test_environment

configure_test_environment()

from nonfunctional.dataset import (  # noqa: E402
    cleanup_database,
    prepare_and_seed,
    verify_seed,
)
from toutiao_backend.config.db_conf import AsyncSessionLocal, engine  # noqa: E402
from toutiao_backend.main import app  # noqa: E402


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def prepared_nonfunctional_environment():
    skip_prepare = os.getenv("NONFUNCTIONAL_SKIP_PREPARE") == "1"
    if skip_prepare:
        await verify_seed()
    else:
        await prepare_and_seed()

    try:
        yield
    finally:
        keep_data = os.getenv("NONFUNCTIONAL_KEEP_DATA") == "1"
        if not keep_data:
            try:
                await cleanup_database()
            except RuntimeError:
                await engine.dispose()
        else:
            await engine.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def api_client(prepared_nonfunctional_environment):
    del prepared_nonfunctional_environment
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        timeout=10,
    ) as client:
        yield client


@pytest_asyncio.fixture(loop_scope="session")
async def db_session(prepared_nonfunctional_environment):
    del prepared_nonfunctional_environment
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="session")
def performance_data() -> dict[str, int | str]:
    return {
        "password": "performance-password",
        "hot_user_id": 1,
        "hot_news_id": 10_000,
        "news_count": 10_000,
        "history_count": 50_000,
    }

