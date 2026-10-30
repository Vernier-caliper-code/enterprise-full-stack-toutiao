from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.db_conf import get_db
from ..crud.news import (
    count_news_by_category,
    get_news_categories,
    get_news_category_by_id,
    get_news_detail,
    get_news_list,
    get_related_news,
    increment_news_views,
)
from ..schemas.news import (
    NewsCategoryOut,
    NewsDetailOut,
    NewsListData,
    NewsListItem,
)
from ..utils.cache import (
    NEWS_CATEGORIES_TTL,
    NEWS_DETAIL_TTL,
    NEWS_LIST_TTL,
    delete_cached_key,
    get_cached_json,
    news_categories_cache_key,
    news_detail_cache_key,
    news_list_cache_key,
    set_cached_json,
)
from ..utils.response import ApiResponse, success_response

router = APIRouter(prefix="/api/news", tags=["新闻"])

categories_adapter = TypeAdapter(list[NewsCategoryOut])


@router.get(
    "/categories",
    response_model=ApiResponse[list[NewsCategoryOut]],
)
async def get_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    cache_key = news_categories_cache_key()
    cached = await get_cached_json(cache_key)
    if cached is None:
        category_rows = await get_news_categories(db)
        categories = [
            NewsCategoryOut.model_validate(category) for category in category_rows
        ]
        await set_cached_json(
            cache_key,
            categories_adapter.dump_json(categories, by_alias=True).decode(),
            NEWS_CATEGORIES_TTL,
        )
    else:
        categories = categories_adapter.validate_json(cached)

    return success_response(data=categories[skip : skip + limit])


@router.get(
    "/list",
    response_model=ApiResponse[NewsListData],
)
async def get_news(
    db: Annotated[AsyncSession, Depends(get_db)],
    category_id: Annotated[int, Query(alias="categoryId", gt=0)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 10,
):
    cache_key = news_list_cache_key(category_id, page, page_size)
    cached = await get_cached_json(cache_key)
    if cached is not None:
        return success_response(data=NewsListData.model_validate_json(cached))

    category = await get_news_category_by_id(db, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="新闻分类不存在",
        )

    total = await count_news_by_category(db, category_id)
    offset = (page - 1) * page_size
    news_rows = await get_news_list(db, category_id, offset, page_size)
    data = NewsListData(
        list=[NewsListItem.model_validate(news) for news in news_rows],
        total=total,
        has_more=offset + len(news_rows) < total,
    )
    await set_cached_json(
        cache_key,
        data.model_dump_json(by_alias=True),
        NEWS_LIST_TTL,
    )
    return success_response(data=data)


@router.get(
    "/detail",
    response_model=ApiResponse[NewsDetailOut],
)
async def get_news_by_id(
    db: Annotated[AsyncSession, Depends(get_db)],
    news_id: Annotated[int, Query(alias="id", gt=0)],
):
    cache_key = news_detail_cache_key(news_id)
    views = await increment_news_views(db, news_id)
    if views is None:
        await delete_cached_key(cache_key)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="新闻不存在",
        )

    cached = await get_cached_json(cache_key)
    if cached is not None:
        data = NewsDetailOut.model_validate_json(cached)
        data.views = views
        await set_cached_json(
            cache_key,
            data.model_dump_json(by_alias=True),
            NEWS_DETAIL_TTL,
        )
        return success_response(data=data)

    news = await get_news_detail(db, news_id)
    if news is None:
        await delete_cached_key(cache_key)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="新闻不存在",
        )

    related_rows = await get_related_news(db, news_id)
    data = NewsDetailOut(
        id=news.id,
        title=news.title,
        content=news.content,
        image=news.image,
        author=news.author,
        publish_time=news.publish_time,
        category_id=news.category_id,
        views=views,
        related_news=[NewsListItem.model_validate(related) for related in related_rows],
    )
    await set_cached_json(
        cache_key,
        data.model_dump_json(by_alias=True),
        NEWS_DETAIL_TTL,
    )
    return success_response(data=data)
