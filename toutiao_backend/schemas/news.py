from datetime import datetime

from pydantic import Field

from .base import PageData, SchemaBase


class NewsCategoryOut(SchemaBase):
    id: int
    created_at: datetime
    updated_at: datetime
    name: str
    sort_order: int


class NewsSummary(SchemaBase):
    id: int
    title: str
    description: str | None = None
    image: str | None = None
    author: str | None = None
    publish_time: datetime
    category_id: int
    views: int


class NewsListItem(NewsSummary):
    created_at: datetime
    updated_at: datetime
    category: NewsCategoryOut | None = None
    content: str


class NewsListData(PageData[NewsListItem]):
    pass


class NewsDetailOut(SchemaBase):
    id: int
    title: str
    content: str
    image: str | None = None
    author: str | None = None
    publish_time: datetime
    category_id: int
    views: int
    related_news: list[NewsListItem] = Field(default_factory=list)
