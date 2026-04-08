"""Integration tests for authentication module."""

import asyncio

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from src.auth.dependencies import get_current_user, get_db
from src.auth.router import router as auth_router
from src.database import Database


def create_test_app() -> FastAPI:
    """Create a test FastAPI application with auth router and protected endpoint."""
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")

    @app.get("/api/v1/auth/me")
    async def get_me(user=Depends(get_current_user)):
        return {
            "id": user.id,
            "username": user.username,
            "created_at": user.created_at.isoformat(),
        }

    return app


@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI application."""
    return create_test_app()


@pytest.fixture
def client(app: FastAPI, db: Database) -> TestClient:
    """Create a test client with database dependency override."""
    app.dependency_overrides[get_db] = lambda: db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class TestSetupEndpoint:
    """Tests for POST /api/v1/auth/setup endpoint."""

    def test_setup_account_success(self, client: TestClient) -> None:
        """Test successful account setup returns JWT token."""
        response = client.post(
            "/api/v1/auth/setup",
            json={"username": "admin", "password": "securepassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 86400

    def test_setup_already_exists(self, client: TestClient) -> None:
        """Test setup fails with 400 when account already exists."""
        # First setup
        client.post(
            "/api/v1/auth/setup",
            json={"username": "admin", "password": "securepassword123"},
        )

        # Second setup attempt
        response = client.post(
            "/api/v1/auth/setup",
            json={"username": "another", "password": "anotherpassword123"},
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_setup_invalid_input(self, client: TestClient) -> None:
        """Test setup with empty username returns validation error."""
        response = client.post(
            "/api/v1/auth/setup",
            json={"username": "", "password": "securepassword123"},
        )

        assert response.status_code == 422


class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login endpoint."""

    def test_login_success(self, client: TestClient) -> None:
        """Test successful login returns JWT token."""
        # Setup account first
        client.post(
            "/api/v1/auth/setup",
            json={"username": "admin", "password": "securepassword123"},
        )

        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "securepassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 86400

    def test_login_wrong_password(self, client: TestClient) -> None:
        """Test login with wrong password returns 401."""
        # Setup account first
        client.post(
            "/api/v1/auth/setup",
            json={"username": "admin", "password": "securepassword123"},
        )

        # Login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient) -> None:
        """Test login with nonexistent user returns 401."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "anypassword"},
        )

        assert response.status_code == 401


class TestLogoutEndpoint:
    """Tests for POST /api/v1/auth/logout endpoint."""

    def test_logout_success(self, client: TestClient) -> None:
        """Test logout endpoint returns success message."""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"


class TestProtectedEndpoint:
    """Tests for protected endpoints using get_current_user dependency."""

    def test_protected_without_token(self, client: TestClient) -> None:
        """Test protected endpoint without token returns 401."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_protected_with_invalid_token(self, client: TestClient) -> None:
        """Test protected endpoint with invalid token returns 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"},
        )

        assert response.status_code == 401

    def test_protected_with_valid_token(self, client: TestClient) -> None:
        """Test protected endpoint with valid token returns 200."""
        # Setup account
        client.post(
            "/api/v1/auth/setup",
            json={"username": "testuser", "password": "testpass123"},
        )

        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        token = login_response.json()["access_token"]

        # Access protected endpoint
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert "id" in data
