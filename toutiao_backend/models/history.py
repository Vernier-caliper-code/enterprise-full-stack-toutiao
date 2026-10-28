from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, ForeignKey, Index, text
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..config.db_conf import Base

if TYPE_CHECKING:
    from .news import News
    from .users import User


class History(Base):
    __tablename__ = "history"
    __table_args__ = (
        Index("fk_history_user_idx", "user_id"),
        Index("fk_history_news_idx", "news_id"),
        Index("idx_view_time", "view_time"),
    )

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "user.id",
            name="fk_history_user",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
    )
    news_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "news.id",
            name="fk_history_news",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
    )
    view_time: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    user: Mapped[User] = relationship(back_populates="histories")
    news: Mapped[News] = relationship(back_populates="histories")
