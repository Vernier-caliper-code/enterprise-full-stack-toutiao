from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.db_conf import get_db
from ..crud.history import (
    clear_user_history,
    create_history,
    delete_history,
    get_user_history,
)
from ..crud.news import get_news_detail
from ..models.history import History
from ..models.users import User
from ..schemas.history import (
    HistoryCreatedOut,
    HistoryItemOut,
    HistoryListData,
    HistoryRequest,
)
from ..utils.auth import get_current_user
from ..utils.cache import (
    HISTORY_LIST_TTL,
    delete_cached_key,
    get_cached_json,
    history_list_cache_key,
    set_cached_json,
)
from ..utils.response import ApiResponse, success_response

router = APIRouter(prefix="/api/history", tags=["浏览历史"])

history_list_adapter = TypeAdapter(list[HistoryItemOut])


def history_item_data(history: History) -> HistoryItemOut:
    news = history.news
    return HistoryItemOut(
        id=history.id,
        title=news.title,
        description=news.description,
        image=news.image,
        author=news.author,
        publish_time=news.publish_time,
        category_id=news.category_id,
        views=news.views,
        view_time=history.view_time,
    )


@router.post(
    "/add",
    response_model=ApiResponse[HistoryCreatedOut],
)
async def add_history(
    payload: HistoryRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    news = await get_news_detail(db, payload.news_id)
    if news is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="新闻不存在",
        )

    history = await create_history(
        db,
        History(
            user_id=current_user.id,
            news_id=payload.news_id,
        ),
    )
    await db.commit()
    await delete_cached_key(history_list_cache_key(current_user.id))

    data = HistoryCreatedOut(
        id=history.id,
        user_id=history.user_id,
        news_id=history.news_id,
        view_time=history.view_time,
    )
    return success_response(message="添加成功", data=data)


@router.get(
    "/list",
    response_model=ApiResponse[HistoryListData],
)
async def get_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 10,
):
    cache_key = history_list_cache_key(current_user.id)
    cached = await get_cached_json(cache_key)
    if cached is None:
        history_rows = await get_user_history(db, current_user.id)
        items = [history_item_data(history) for history in history_rows]
        await set_cached_json(
            cache_key,
            history_list_adapter.dump_json(
                items,
                by_alias=True,
            ).decode(),
            HISTORY_LIST_TTL,
        )
    else:
        items = history_list_adapter.validate_json(cached)

    offset = (page - 1) * page_size
    total = len(items)
    data = HistoryListData(
        list=items[offset : offset + page_size],
        total=total,
        has_more=offset + page_size < total,
    )
    return success_response(data=data)


@router.delete(
    "/delete/{history_id}",
    response_model=ApiResponse[None],
)
async def delete_history_item(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    history_id: Annotated[int, Path(gt=0)],
):
    deleted = await delete_history(db, current_user.id, history_id)
    if not deleted:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="浏览记录不存在",
        )

    await db.commit()
    await delete_cached_key(history_list_cache_key(current_user.id))
    return success_response(message="删除成功", data=None)


@router.delete(
    "/clear",
    response_model=ApiResponse[None],
)
async def clear_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await clear_user_history(db, current_user.id)
    await db.commit()
    await delete_cached_key(history_list_cache_key(current_user.id))
    return success_response(message="清空成功", data=None)
