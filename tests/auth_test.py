import pytest
from jose import jwt

from app.auth.schemas import TokenSchema
from app.roles.utils import create_default_roles
from app.scopes.utils import create_scopes
from app.settings import get_settings
from app.users.models import User
from tests.conftest import create_fake_users

TEST_REGISTER_USER = {
    "username": "Test",
    "email": "test@test.pl",
    "password": "testpassword123",
    "password2": "testpassword123"
}

TEST_LOGIN_USER = {
    "username": TEST_REGISTER_USER['username'],
    "password": TEST_REGISTER_USER['password']
}


@pytest.mark.asyncio
async def test_auth_register(client):
    await create_scopes()
    await create_default_roles()
    r = await client.post("/auth/register", json=TEST_REGISTER_USER)
    assert r.status_code == 200
    assert len(await User.objects.all()) == 1
    assert r.json()['username'] == "Test"
    assert "password" not in r.json()
    assert r.json()["is_activated"] is False
    assert r.json()["is_superuser"] is False

    assert len(r.json()["roles"]) == 1
    assert r.json()["display_role"]["id"] == 2


@pytest.mark.asyncio
async def test_auth_register_exception_when_password_not_match(client):
    await create_scopes()
    await create_default_roles()
    r = await client.post("/auth/register", json={
        "username": TEST_REGISTER_USER['username'],
        "email": TEST_REGISTER_USER['email'],
        "password": TEST_REGISTER_USER['password'],
        "password2": "diffrentpassword"
    })
    response_data = {
        "detail": [
            {
                'loc': ['body', 'password2'], 'msg': 'Passwords do not match', 'type': 'value_error'
            }
        ]
    }

    assert r.status_code == 422
    assert r.json() == response_data


@pytest.mark.asyncio
async def test_auth_register_exception_when_username_or_password_is_taken(client, faker):
    users = await create_fake_users(faker, 1)
    user = users[0]
    r = await client.post("/auth/register", json={
        "username": user.username,
        "email": user.email,
        "password": TEST_REGISTER_USER['password'],
        "password2": TEST_REGISTER_USER['password2']
    })
    assert r.status_code == 422
    assert r.json()["detail"] == "Email or username already exists"


@pytest.mark.asyncio
async def test_auth_create_access_token(client):
    await create_scopes()
    await create_default_roles()
    r = await client.post("/auth/register", json=TEST_REGISTER_USER)
    data = r.json()
    r = await client.post("/auth/token", data=TEST_LOGIN_USER)
    assert r.status_code == 200
    assert "access_token" in r.json()
    assert "refresh_token" in r.json()
    assert "token_type" in r.json()


@pytest.mark.asyncio
async def test_get_access_token_from_refresh_token(client, faker):
    await create_scopes()
    await create_default_roles()
    await client.post("/auth/register", json=TEST_REGISTER_USER)
    r = await client.post("/auth/token", data=TEST_LOGIN_USER)
    token_data = r.json()

    r_r = await client.post("/auth/token/refresh", json={
        "refresh_token": token_data["refresh_token"]
    })
    assert r_r.status_code == 200
