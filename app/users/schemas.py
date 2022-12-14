from enum import Enum
from typing import Optional, List

from aioredis import Redis
from fastapi_events.registry.payload_schema import registry as payload_schema
from pydantic import BaseModel, validator

from app.auth.enums import AuthEventsEnum
from app.steamprofile.models import SteamProfile
from app.steamprofile.schemas import SteamPlayer
from app.users.models import User

UserOut = User.get_pydantic(exclude={"password", "email"})
UserOutWithEmail = User.get_pydantic(exclude={"password"})


class UserInSchema(BaseModel):
    username: str
    email: str
    password: str


class UserOutRoleSchema(BaseModel):
    id: int
    name: Optional[str] = None
    color: Optional[str] = None
    is_staff: Optional[bool] = None


class UserOut2Schema(BaseModel):
    id: int
    username: Optional[str] = None
    avatar: Optional[str] = None
    display_role: Optional[UserOutRoleSchema] = None
    roles: Optional[List[UserOutRoleSchema]] = None
    steamprofile: Optional[SteamPlayer] = None


class ChangeUsernameSchema(BaseModel):
    username: str


class ChangePasswordSchema(BaseModel):
    current_password: str
    new_password: str
    new_password2: str

    @validator('new_password2')
    def passwords_match(cls, value, values, **kwargs):
        if "new_password" in values and value != values["new_password"]:
            raise ValueError("Passwords do not match")


class ChangeDisplayRoleSchema(BaseModel):
    role_id: int


class CreateUserSchema(BaseModel):
    username: str
    email: str
    password: str
    display_role: Optional[int] = None
    roles: Optional[List[int]] = None
    is_activated: bool = True
