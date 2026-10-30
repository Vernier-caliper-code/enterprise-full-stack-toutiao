from typing import Literal

from .base import SchemaBase

Gender = Literal["male", "female", "unknown"]


class UserRegisterRequest(SchemaBase):
    username: str
    password: str


class UserLoginRequest(SchemaBase):
    username: str
    password: str


class UserUpdateRequest(SchemaBase):
    nickname: str | None = None
    avatar: str | None = None
    gender: Gender | None = None
    bio: str | None = None
    phone: str | None = None


class UserPasswordUpdateRequest(SchemaBase):
    old_password: str
    new_password: str


class UserInfo(SchemaBase):
    id: int
    username: str
    nickname: str | None = None
    avatar: str | None = None
    gender: Gender | None = None
    bio: str | None = None


class UserAuthData(SchemaBase):
    token: str
    user_info: UserInfo
