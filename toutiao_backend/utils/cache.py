from ..config.cache_conf import redis_client

NEWS_DETAIL_TTL = 60 * 60
NEWS_LIST_TTL = 30 * 60
NEWS_CATEGORIES_TTL = 2 * 60 * 60
HISTORY_LIST_TTL = 60 * 60


def news_categories_cache_key() -> str:
    return "news:categories"


def news_list_cache_key(category_id: int, page: int, page_size: int) -> str:
    return f"news:list:{category_id}:{page}:{page_size}"


def news_detail_cache_key(news_id: int) -> str:
    return f"news:detail:{news_id}"


def history_list_cache_key(user_id: int) -> str:
    return f"history:list:{user_id}"


async def get_cached_json(key: str) -> str | None:
    return await redis_client.get(key)


async def set_cached_json(key: str, value: str, ttl: int) -> None:
    await redis_client.set(key, value, ex=ttl)


async def delete_cached_key(key: str) -> None:
    await redis_client.delete(key)
