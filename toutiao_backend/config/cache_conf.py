import os
from collections.abc import AsyncGenerator

from redis.asyncio import Redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None

redis_client = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True,
    protocol=2,
    socket_connect_timeout=3,
    socket_timeout=3,
)


async def get_redis() -> AsyncGenerator[Redis, None]:
    yield redis_client


async def close_redis() -> None:
    await redis_client.aclose()
