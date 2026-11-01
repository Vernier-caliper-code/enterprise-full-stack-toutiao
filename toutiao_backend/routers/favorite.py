from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.db_conf import get_db
from ..crud.favorite import (
    clear_user_favorites,
    count_user_favorites,
    create_favorite,
    delete_favorite,
    get_favorite,
    get_user_favorites,
)
from ..crud.news import get_news_detail
from ..models.favorite import Favorite
from ..models.news import News
from ..models.users import User
from ..schemas.favorite import (
    FavoriteCreatedOut,
    FavoriteItemOut,
    FavoriteListData,
    FavoriteRequest,
    FavoriteStatusOut,
)
from ..utils.auth import get_current_user
from ..utils.response import ApiResponse, success_response

router = APIRouter(prefix="/api/favorite", tags=["收藏"])


def favorite_created_data(
    favorite: Favorite,
    news_id: int,
) -> FavoriteCreatedOut:
    return FavoriteCreatedOut(
        id=favorite.id,
        user_id=favorite.user_id,
        news_id=news_id,
        create_time=favorite.created_at,
    )


def favorite_item_data(favorite: Favorite) -> FavoriteItemOut:
    news = favorite.news
    return FavoriteItemOut(
        id=favorite.id,
        news_id=news.id,
        title=news.title,
        description=news.description,
        image=news.image,
        author=news.author,
        publish_time=news.publish_time,
        category_id=news.category_id,
        views=news.views,
        favorite_time=favorite.created_at,
    )


async def find_news_or_404(
    db: AsyncSession,
    news_id: int,
) -> News:
    news = await get_news_detail(db, news_id)
    if news is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="新闻不存在",
        )
    return news


@router.get(
    "/check",
    response_model=ApiResponse[FavoriteStatusOut],
)
async def check_favorite(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    news_id: Annotated[int, Query(alias="newsId", gt=0)],
):
    favorite = await get_favorite(db, current_user.id, news_id)
    return success_response(
        data=FavoriteStatusOut(is_favorite=favorite is not None),
    )


@router.post(
    "/add",
    response_model=ApiResponse[FavoriteCreatedOut],
)
async def add_favorite(
    payload: FavoriteRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await find_news_or_404(db, payload.news_id)
    favorite = await get_favorite(db, current_user.id, payload.news_id)
    if favorite is not None:
        return success_response(
            message="收藏成功",
            data=favorite_created_data(favorite, payload.news_id),
        )

    favorite = Favorite(
        user_id=current_user.id,
        news_id=payload.news_id,
    )
    try:
        favorite = await create_favorite(db, favorite)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        favorite = await get_favorite(db, current_user.id, payload.news_id)
        if favorite is None:
            raise

    return success_response(
        message="收藏成功",
        data=favorite_created_data(favorite, payload.news_id),
    )


@router.delete(
    "/remove",
    response_model=ApiResponse[None],
)
async def remove_favorite(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    news_id: Annotated[int, Query(alias="newsId", gt=0)],
):
    await delete_favorite(db, current_user.id, news_id)
    await db.commit()
    return success_response(message="取消收藏成功", data=None)


@router.get(
    "/list",
    response_model=ApiResponse[FavoriteListData],
)
async def get_favorites(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 10,
):
    total = await count_user_favorites(db, current_user.id)
    offset = (page - 1) * page_size
    favorites = await get_user_favorites(
        db,
        current_user.id,
        offset,
        page_size,
    )
    data = FavoriteListData(
        list=[favorite_item_data(favorite) for favorite in favorites],
        total=total,
        has_more=offset + len(favorites) < total,
    )
    return success_response(data=data)


@router.delete(
    "/clear",
    response_model=ApiResponse[None],
)
async def clear_favorites(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    count = await clear_user_favorites(db, current_user.id)
    await db.commit()
    return success_response(
        message=f"成功删除{count}条收藏记录",
        data=None,
    )
