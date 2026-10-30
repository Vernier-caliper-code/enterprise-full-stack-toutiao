from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.db_conf import get_db
from ..crud.users import (
    create_user,
    create_user_token,
    get_user_by_username,
    update_user,
    update_user_password,
)
from ..models.users import User
from ..schemas.users import (
    UserAuthData,
    UserInfo,
    UserLoginRequest,
    UserPasswordUpdateRequest,
    UserRegisterRequest,
    UserUpdateRequest,
)
from ..utils.auth import get_current_user
from ..utils.response import ApiResponse, success_response
from ..utils.security import (
    generate_token,
    hash_password,
    token_expires_at,
    verify_password,
)

router = APIRouter(prefix="/api/user", tags=["用户"])

DEFAULT_AVATAR = "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
DEFAULT_BIO = "这个人很懒，什么都没留下"


@router.post(
    "/register",
    response_model=ApiResponse[UserAuthData],
)
async def register(
    payload: UserRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if await get_user_by_username(db, payload.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    user = User(
        username=payload.username,
        password=hash_password(payload.password),
        avatar=DEFAULT_AVATAR,
        gender="unknown",
        bio=DEFAULT_BIO,
    )

    try:
        user = await create_user(db, user)
        token = generate_token()
        user_token = await create_user_token(
            db,
            user.id,
            token,
            token_expires_at(),
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        ) from None

    data = UserAuthData(
        token=user_token.token,
        user_info=UserInfo.model_validate(user),
    )
    return success_response(message="注册成功", data=data)


@router.post(
    "/login",
    response_model=ApiResponse[UserAuthData],
)
async def login(
    payload: UserLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await get_user_by_username(db, payload.username)
    if user is None or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    user_token = await create_user_token(
        db,
        user.id,
        generate_token(),
        token_expires_at(),
    )
    await db.commit()

    data = UserAuthData(
        token=user_token.token,
        user_info=UserInfo.model_validate(user),
    )
    return success_response(message="登录成功", data=data)


@router.get(
    "/info",
    response_model=ApiResponse[UserInfo],
)
async def get_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return success_response(data=UserInfo.model_validate(current_user))


@router.put(
    "/update",
    response_model=ApiResponse[UserInfo],
)
async def update_user_info(
    payload: UserUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    user = await update_user(
        db,
        current_user,
        payload.model_dump(exclude_unset=True),
    )
    await db.commit()
    return success_response(
        message="更新成功",
        data=UserInfo.model_validate(user),
    )


@router.put(
    "/password",
    response_model=ApiResponse[None],
)
async def update_password(
    payload: UserPasswordUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not verify_password(payload.old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误",
        )

    await update_user_password(
        db,
        current_user,
        hash_password(payload.new_password),
    )
    await db.commit()
    return success_response(message="密码修改成功", data=None)
