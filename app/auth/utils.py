import asyncio
import random
import string
from datetime import timedelta, datetime
from sqlite3 import IntegrityError as SQLIntegrityError
from typing import Optional, Dict

from asyncpg import UniqueViolationError
from cryptography.fernet import Fernet
from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2, SecurityScopes
from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from starlette import status
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED

from app.auth.exceptions import credentials_exception, invalid_username_password_exception, inactive_user_exception
from app.auth.schemas import TokenData, RegisterUser
from app.roles.models import Role
from app.scopes.utils import get_scopes
from app.settings import Settings, get_settings
from app.users.exceptions import UserNotFound
from app.users.models import User
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

crypto_key = Fernet.generate_key()

fernet = Fernet(crypto_key)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(plain_password):
    return pwd_context.hash(plain_password)


async def authenticate_user(username: str, password: str) -> User | bool:
    try:
        user = await User.objects.select_related(["roles", "roles__scopes"]).get(username=username)
        if not verify_password(password, user.password):
            return False
    except UserNotFound as e:
        return False
    return user


def create_access_token(settings: Settings = Depends(get_settings), data: dict = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme),
                           settings: Settings = Depends(get_settings)):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(user_id=user_id, scopes=token_scopes)
    except JWTError as e:
        raise credentials_exception
    try:
        user = await User.objects.select_related(["roles", "display_role"]).get(
            id=int(token_data.user_id))
    except UserNotFound:
        raise invalid_username_password_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user


async def get_current_active_user(current_user: User = Security(get_current_user, scopes=["users:me"])):
    if not current_user.is_activated:
        raise inactive_user_exception
    return current_user


async def register_user(user_data: RegisterUser):
    password = get_password_hash(user_data.password)
    try:
        user_role = await Role.objects.get(id=2)
        created_user = await User.objects.create(
            username=user_data.username,
            email=user_data.email,
            password=password,
            display_role=user_role
        )

        await created_user.roles.add(user_role)
    except (IntegrityError, SQLIntegrityError, UniqueViolationError) as e:
        raise HTTPException(status_code=422, detail=f"Email or username already exists")

    return created_user


def generate_code(number: int = 8):
    return ''.join(random.choice(string.digits) for _ in range(number))