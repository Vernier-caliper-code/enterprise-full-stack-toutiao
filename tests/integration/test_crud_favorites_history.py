import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from toutiao_backend.crud.favorite import (
    clear_user_favorites,
    count_user_favorites,
    create_favorite,
    delete_favorite,
    get_favorite,
    get_user_favorites,
)
from toutiao_backend.crud.history import (
    clear_user_history,
    create_history,
    delete_history,
    get_user_history,
)
from toutiao_backend.models.favorite import Favorite
from toutiao_backend.models.history import History
from toutiao_backend.models.users import User
from toutiao_backend.utils.security import hash_password

pytestmark = pytest.mark.integration


async def _create_test_user(db_session: AsyncSession, username: str) -> User:
    user = User(
        username=username,
        password=hash_password("secret"),
        gender="unknown",
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def test_favorite_crud_and_user_isolation(
    db_session: AsyncSession,
    catalog: dict,
) -> None:
    # Arrange
    user = await _create_test_user(db_session, "FAVORITE_USER")
    other_user = await _create_test_user(db_session, "OTHER_USER")
    news_id = catalog["latest"].id
    other_news_id = catalog["older"].id

    # Act
    favorite = await create_favorite(
        db_session,
        Favorite(user_id=user.id, news_id=news_id),
    )
    await create_favorite(
        db_session,
        Favorite(user_id=other_user.id, news_id=other_news_id),
    )

    # Assert
    assert await get_favorite(db_session, user.id, news_id) is not None
    assert await count_user_favorites(db_session, user.id) == 1
    favorites = await get_user_favorites(db_session, user.id, 0, 10)
    assert [item.id for item in favorites] == [favorite.id]
    assert favorites[0].news.id == news_id


async def test_delete_and_clear_favorites_only_affect_owner(
    db_session: AsyncSession,
    catalog: dict,
) -> None:
    # Arrange
    user = await _create_test_user(db_session, "DELETE_FAVORITE_USER")
    other_user = await _create_test_user(db_session, "KEEP_FAVORITE_USER")
    await create_favorite(
        db_session,
        Favorite(user_id=user.id, news_id=catalog["latest"].id),
    )
    await create_favorite(
        db_session,
        Favorite(user_id=user.id, news_id=catalog["older"].id),
    )
    await create_favorite(
        db_session,
        Favorite(user_id=other_user.id, news_id=catalog["latest"].id),
    )

    # Act
    deleted = await delete_favorite(db_session, user.id, catalog["latest"].id)
    deleted_again = await delete_favorite(
        db_session,
        user.id,
        catalog["latest"].id,
    )
    cleared_count = await clear_user_favorites(db_session, user.id)

    # Assert
    assert deleted is True
    assert deleted_again is False
    assert cleared_count == 1
    assert await count_user_favorites(db_session, user.id) == 0
    assert await count_user_favorites(db_session, other_user.id) == 1


async def test_history_crud_and_owner_scope(
    db_session: AsyncSession,
    catalog: dict,
) -> None:
    # Arrange
    user = await _create_test_user(db_session, "HISTORY_USER")
    other_user = await _create_test_user(db_session, "OTHER_HISTORY_USER")
    first = await create_history(
        db_session,
        History(user_id=user.id, news_id=catalog["latest"].id),
    )
    await create_history(
        db_session,
        History(user_id=user.id, news_id=catalog["older"].id),
    )
    await create_history(
        db_session,
        History(user_id=other_user.id, news_id=catalog["sports_news"].id),
    )

    # Act
    history = await get_user_history(db_session, user.id)
    deleted = await delete_history(db_session, other_user.id, first.id)
    deleted_as_owner = await delete_history(db_session, user.id, first.id)
    cleared = await clear_user_history(db_session, user.id)

    # Assert
    assert len(history) == 2
    assert deleted is False
    assert deleted_as_owner is True
    assert cleared == 1
    assert await get_user_history(db_session, user.id) == []
    assert len(await get_user_history(db_session, other_user.id)) == 1
