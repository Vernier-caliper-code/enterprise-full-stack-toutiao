from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_DATABASE = "news_app_test"
TEST_REDIS_DB = 15

NEWS_COUNT = 10_000
CATEGORY_COUNT = 8
USER_COUNT = 50
FAVORITE_COUNT = 20_000
HISTORY_COUNT = 50_000
HOT_USER_ID = 1
HOT_HISTORY_COUNT = 10_000

PERFORMANCE_PASSWORD = "performance-password"
TOKEN_PREFIX = "perf-token-"


def configure_test_environment() -> None:
    load_dotenv(PROJECT_ROOT / ".env.test.local")
    os.environ["MYSQL_DATABASE"] = TEST_DATABASE
    os.environ["REDIS_DB"] = str(TEST_REDIS_DB)


def artifact_root() -> Path:
    configured = os.getenv("NONFUNCTIONAL_ARTIFACT_DIR")
    path = Path(configured) if configured else PROJECT_ROOT / "nonfunctional" / "artifacts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def performance_token(user_id: int) -> str:
    return f"{TOKEN_PREFIX}{user_id:02d}-" + ("x" * 40)
