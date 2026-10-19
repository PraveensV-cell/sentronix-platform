import os
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

os.environ.update(
    {
        "APP_NAME": "Sentronix API Tests",
        "APP_VERSION": "test",
        "ENVIRONMENT": "test",
        "HOST": "127.0.0.1",
        "PORT": "8000",
        "DEBUG": "false",
        "API_PREFIX": "/api/v1",
        "API_DESCRIPTION": "Test API",
        "CONTACT_NAME": "Test",
        "CONTACT_EMAIL": "test@example.com",
        "LICENSE_NAME": "MIT",
        "JWT_SECRET_KEY": "test-only-secret-not-for-production",
        "JWT_ALGORITHM": "HS256",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "15",
        "DATABASE_HOST": "localhost",
        "DATABASE_PORT": "5432",
        "DATABASE_NAME": "sentronix_test",
        "DATABASE_USER": "test",
        "DATABASE_PASSWORD": "test-only",
        "DATABASE_URL": "sqlite://",
        "SMTP_HOST": "localhost",
        "SMTP_PORT": "1025",
        "SMTP_USERNAME": "",
        "SMTP_PASSWORD": "",
        "SMTP_FROM": "no-reply@example.com",
        "ADMIN_EMAIL": "admin@example.com",
    }
)

from src.api.v1.endpoints import auth as auth_routes
from src.api.v1.endpoints import users as user_routes
from src.dependencies.auth import get_current_user
from src.database.session import get_db
from src.schemas.user import UserRegistration
from src.services import auth as auth_service_module
from src.services import user as user_service_module
from src.services.user import UserService


def build_client():
    app = FastAPI()
    app.include_router(auth_routes.router)
    app.include_router(user_routes.router)
    app.dependency_overrides[get_db] = lambda: object()
    return TestClient(app), app


def test_public_registration_schema_rejects_role_escalation():
    with pytest.raises(ValidationError):
        UserRegistration(
            username="new-user",
            email="new-user@example.com",
            full_name="New User",
            password="long-enough-password",
            role="super_admin",
        )


def test_registration_service_always_assigns_viewer(monkeypatch):
    class FakeUser:
        def __init__(self, **fields):
            self.__dict__.update(fields)

    class FakeRepository:
        def __init__(self, _db):
            pass

        def get_by_username(self, _username):
            return None

        def get_by_email(self, _email):
            return None

        def create(self, user):
            return user

    monkeypatch.setattr(user_service_module, "User", FakeUser)
    monkeypatch.setattr(user_service_module, "UserRepository", FakeRepository)
    monkeypatch.setattr(user_service_module, "hash_password", lambda _password: "hashed")

    registration = UserRegistration(
        username="new-user",
        email="new-user@example.com",
        full_name="New User",
        password="long-enough-password",
    )

    user = UserService(object()).register_user(registration)

    assert user.role == "viewer"
    assert user.hashed_password == "hashed"


def test_user_management_requires_authentication():
    client, _app = build_client()

    response = client.get("/users")

    assert response.status_code in (401, 403)


def test_non_admin_cannot_list_users(monkeypatch):
    client, app = build_client()
    app.dependency_overrides[get_current_user] = lambda: {
        "sub": "operator",
        "role": "operator",
    }

    class FakeUserService:
        def __init__(self, _db):
            pass

        def list_users(self):
            pytest.fail("The endpoint must reject non-admins before listing users.")

    monkeypatch.setattr(user_routes, "UserService", FakeUserService)

    response = client.get("/users")

    assert response.status_code == 403


def test_non_admin_cannot_create_privileged_user(monkeypatch):
    client, app = build_client()
    app.dependency_overrides[get_current_user] = lambda: {
        "sub": "operator",
        "role": "operator",
    }

    class FakeUserService:
        def __init__(self, _db):
            pass

        def create_user(self, _request):
            pytest.fail("The endpoint must reject non-admins before creating users.")

    monkeypatch.setattr(user_routes, "UserService", FakeUserService)

    response = client.post(
        "/users",
        json={
            "username": "new-admin",
            "email": "new-admin@example.com",
            "full_name": "New Admin",
            "password": "long-enough-password",
            "role": "super_admin",
        },
    )

    assert response.status_code == 403


def test_non_admin_cannot_delete_users(monkeypatch):
    client, app = build_client()
    app.dependency_overrides[get_current_user] = lambda: {
        "sub": "operator",
        "role": "operator",
    }

    class FakeUserService:
        def __init__(self, _db):
            pass

        def delete_user(self, _user_id):
            pytest.fail("The endpoint must reject non-admins before deleting users.")

    monkeypatch.setattr(user_routes, "UserService", FakeUserService)

    response = client.delete("/users/42")

    assert response.status_code == 403


def test_super_admin_can_list_users(monkeypatch):
    client, app = build_client()
    app.dependency_overrides[get_current_user] = lambda: {
        "sub": "admin",
        "role": "super_admin",
    }

    class FakeUserService:
        def __init__(self, _db):
            pass

        def list_users(self):
            return []

    monkeypatch.setattr(user_routes, "UserService", FakeUserService)

    response = client.get("/users")

    assert response.status_code == 200
    assert response.json() == []


def test_registration_endpoint_returns_viewer_account(monkeypatch):
    client, _app = build_client()
    user = SimpleNamespace(
        id=1,
        username="new-user",
        email="new-user@example.com",
        full_name="New User",
        role="viewer",
        is_active=True,
        created_at=datetime.now(UTC),
    )

    class FakeUserService:
        def __init__(self, _db):
            pass

        def register_user(self, _request):
            return user

    monkeypatch.setattr(auth_routes, "UserService", FakeUserService)

    response = client.post(
        "/auth/register",
        json={
            "username": "new-user",
            "email": "new-user@example.com",
            "full_name": "New User",
            "password": "long-enough-password",
        },
    )

    assert response.status_code == 201
    assert response.json()["role"] == "viewer"


def test_inactive_user_cannot_login(monkeypatch):
    inactive_user = SimpleNamespace(
        username="inactive",
        role="viewer",
        hashed_password="hash",
        is_active=False,
    )

    class FakeUserService:
        def __init__(self, _db):
            pass

        def authenticate_user(self, _username):
            return inactive_user

    monkeypatch.setattr(auth_service_module, "UserService", FakeUserService)
    monkeypatch.setattr(auth_service_module, "verify_password", lambda *_args: True)

    result = auth_service_module.AuthenticationService(object()).authenticate(
        "inactive",
        "correct-password",
    )

    assert result is None


def test_invalid_token_is_rejected_with_401():
    client, _app = build_client()

    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )

    assert response.status_code == 401
