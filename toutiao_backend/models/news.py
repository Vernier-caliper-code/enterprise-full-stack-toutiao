from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..config.db_conf import Base

if TYPE_CHECKING:
    from .favorite import Favorite
    from .history import History


class NewsCategory(Base):
    __tablename__ = "news_category"
    __table_args__ = (Index("name_UNIQUE", "name", unique=True),)

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sort_order: Mapped[int] = mapped_column(nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )

    news_items: Mapped[list[News]] = relationship(back_populates="category")


class News(Base):
    __tablename__ = "news"
    __table_args__ = (
        Index("fk_news_category_idx", "category_id"),
        Index("idx_publish_time", "publish_time"),
    )

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image: Mapped[str | None] = mapped_column(String(255))
    author: Mapped[str | None] = mapped_column(String(50))
    category_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "news_category.id",
            name="fk_news_category",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        nullable=False,
    )
    views: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        server_default=text("0"),
    )
    publish_time: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )

    category: Mapped[NewsCategory] = relationship(back_populates="news_items")
    related_links: Mapped[list[RelatedNews]] = relationship(
        foreign_keys="RelatedNews.news_id",
        back_populates="news",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    related_to_links: Mapped[list[RelatedNews]] = relationship(
        foreign_keys="RelatedNews.related_news_id",
        back_populates="related_news",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    favorites: Mapped[list[Favorite]] = relationship(
        back_populates="news",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    histories: Mapped[list[History]] = relationship(
        back_populates="news",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class RelatedNews(Base):
    __tablename__ = "related_news"
    __table_args__ = (
        Index("news_related_unique", "news_id", "related_news_id", unique=True),
        Index("fk_related_news_news_idx", "news_id"),
        Index("fk_related_news_related_idx", "related_news_id"),
    )

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    news_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "news.id",
            name="fk_related_news_news",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
    )
    related_news_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "news.id",
            name="fk_related_news_related",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    news: Mapped[News] = relationship(
        foreign_keys=[news_id],
        back_populates="related_links",
    )
    related_news: Mapped[News] = relationship(
        foreign_keys=[related_news_id],
        back_populates="related_to_links",
    )
