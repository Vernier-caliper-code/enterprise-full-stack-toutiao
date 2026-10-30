from toutiao_backend.utils.cache import (
    history_list_cache_key,
    news_categories_cache_key,
    news_detail_cache_key,
    news_list_cache_key,
)


def test_cache_keys_match_the_documented_contract() -> None:
    # Arrange
    category_id = 3
    page = 2
    page_size = 20
    news_id = 42
    user_id = 9

    # Act
    keys = {
        "categories": news_categories_cache_key(),
        "list": news_list_cache_key(category_id, page, page_size),
        "detail": news_detail_cache_key(news_id),
        "history": history_list_cache_key(user_id),
    }

    # Assert
    assert keys == {
        "categories": "news:categories",
        "list": "news:list:3:2:20",
        "detail": "news:detail:42",
        "history": "history:list:9",
    }
