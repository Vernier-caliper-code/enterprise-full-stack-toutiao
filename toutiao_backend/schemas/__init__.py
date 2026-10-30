from .base import PageData, SchemaBase
from .favorite import (
    FavoriteCreatedOut,
    FavoriteItemOut,
    FavoriteListData,
    FavoriteRequest,
    FavoriteStatusOut,
)
from .history import (
    HistoryCreatedOut,
    HistoryItemOut,
    HistoryListData,
    HistoryRequest,
)
from .news import (
    NewsCategoryOut,
    NewsDetailOut,
    NewsListData,
    NewsListItem,
    NewsSummary,
)
from .users import (
    Gender,
    UserAuthData,
    UserInfo,
    UserLoginRequest,
    UserPasswordUpdateRequest,
    UserRegisterRequest,
    UserUpdateRequest,
)

__all__ = [
    "FavoriteCreatedOut",
    "FavoriteItemOut",
    "FavoriteListData",
    "FavoriteRequest",
    "FavoriteStatusOut",
    "Gender",
    "HistoryCreatedOut",
    "HistoryItemOut",
    "HistoryListData",
    "HistoryRequest",
    "NewsCategoryOut",
    "NewsDetailOut",
    "NewsListData",
    "NewsListItem",
    "NewsSummary",
    "PageData",
    "SchemaBase",
    "UserAuthData",
    "UserInfo",
    "UserLoginRequest",
    "UserPasswordUpdateRequest",
    "UserRegisterRequest",
    "UserUpdateRequest",
]
