from datetime import datetime

from .base import PageData, SchemaBase
from .news import NewsSummary


class FavoriteRequest(SchemaBase):
    news_id: int


class FavoriteStatusOut(SchemaBase):
    is_favorite: bool


class FavoriteCreatedOut(SchemaBase):
    id: int
    user_id: int
    news_id: int
    create_time: datetime


class FavoriteItemOut(NewsSummary):
    news_id: int
    favorite_time: datetime


class FavoriteListData(PageData[FavoriteItemOut]):
    pass
