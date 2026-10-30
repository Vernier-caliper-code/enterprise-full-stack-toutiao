from datetime import datetime

from .base import PageData, SchemaBase
from .news import NewsSummary


class HistoryRequest(SchemaBase):
    news_id: int


class HistoryCreatedOut(SchemaBase):
    id: int
    user_id: int
    news_id: int
    view_time: datetime


class HistoryItemOut(NewsSummary):
    view_time: datetime


class HistoryListData(PageData[HistoryItemOut]):
    pass
