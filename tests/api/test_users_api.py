import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from toutiao_backend.utils.security import verify_password

pytestmark = pytest.mark.api


async def test_register_returns_token_and_default_profile(
    app_client: AsyncClient,
) -> None:
    # Arrange
    payload = {"username": "API_REGISTER_USER", "password": "secret-123"}

    # Act
    response = await app_client.post("/api/user/register", json=payload)
    duplicate = await app_client.post("/api/user/register", json=payload)

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    assert body["message"] == "注册成功"
    assert body["data"]["token"]
    assert body["data"]["userInfo"]["username"] == "API_REGISTER_USER"
    assert body["data"]["userInfo"]["gender"] == "unknown"
    assert duplicate.status_code == 400
    assert duplicate.json()["message"] == "用户名已存在"


async def test_login_returns_new_token_for_valid_credentials(
    app_client: AsyncClient,
    user_with_token: dict,
) -> None:
    # Arrange
    payload = {"username": "TEST_USER", "password": "test-password"}

    # Act
    response = await app_client.post("/api/user/login", json=payload)
    invalid = await app_client.post(
        "/api/user/login",
        json={"username": "TEST_USER", "password": "wrong-password"},
    )

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "登录成功"
    assert body["data"]["token"] != user_with_token["token"]
    assert body["data"]["userInfo"]["username"] == "TEST_USER"
    assert invalid.status_code == 401
    assert invalid.json()["message"] == "用户名或密码错误"


async def test_get_user_info_requires_valid_token(
    app_client: AsyncClient,
    user_with_token: dict,
) -> None:
    # Arrange
    headers = user_with_token["headers"]

    # Act
    unauthorized = await app_client.get("/api/user/info")
    response = await app_client.get("/api/user/info", headers=headers)

    # Assert
    assert unauthorized.status_code == 401
    assert unauthorized.json()["message"] == "未登录或登录已过期"
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "TEST_USER"


async def test_update_user_info_persists_selected_fields(
    app_client: AsyncClient,
    db_session: AsyncSession,
    user_with_token: dict,
) -> None:
    # Arrange
    payload = {
        "nickname": "API 昵称",
        "bio": "API 更新后的简介",
        "gender": "female",
        "phone": "13800000000",
    }

    # Act
    response = await app_client.put(
        "/api/user/update",
        json=payload,
        headers=user_with_token["headers"],
    )
    await db_session.refresh(user_with_token["user"])

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "更新成功"
    assert body["data"]["nickname"] == "API 昵称"
    assert body["data"]["bio"] == "API 更新后的简介"
    assert body["data"]["gender"] == "female"
    assert user_with_token["user"].phone == "13800000000"


async def test_change_password_updates_login_credentials(
    app_client: AsyncClient,
    db_session: AsyncSession,
    user_with_token: dict,
) -> None:
    # Arrange
    payload = {
        "oldPassword": "test-password",
        "newPassword": "new-test-password",
    }

    # Act
    response = await app_client.put(
        "/api/user/password",
        json=payload,
        headers=user_with_token["headers"],
    )
    await db_session.refresh(user_with_token["user"])
    new_login = await app_client.post(
        "/api/user/login",
        json={"username": "TEST_USER", "password": "new-test-password"},
    )
    old_login = await app_client.post(
        "/api/user/login",
        json={"username": "TEST_USER", "password": "test-password"},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == "密码修改成功"
    assert verify_password(
        "new-test-password",
        user_with_token["user"].password,
    )
    assert new_login.status_code == 200
    assert old_login.status_code == 401
