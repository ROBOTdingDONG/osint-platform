"""
Tests for authentication endpoints
"""

import pytest
from httpx import AsyncClient
from fastapi import status

from app.db.models.user import User


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    async def test_register_user(self, async_client: AsyncClient):
        """Test user registration."""
        user_data = {
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User",
            "company": "New Company"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data
    
    async def test_register_duplicate_email(self, async_client: AsyncClient, test_user: User):
        """Test registration with duplicate email."""
        user_data = {
            "email": test_user.email,
            "password": "password123",
            "full_name": "Duplicate User"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"]
    
    async def test_login_valid_credentials(self, async_client: AsyncClient, test_user: User):
        """Test login with valid credentials."""
        login_data = {
            "email": test_user.email,
            "password": "testpassword123"
        }
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == str(test_user.id)
    
    async def test_login_invalid_credentials(self, async_client: AsyncClient, test_user: User):
        """Test login with invalid credentials."""
        login_data = {
            "email": test_user.email,
            "password": "wrongpassword"
        }
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]
    
    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """Test login with nonexistent user."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_get_current_user(self, async_client: AsyncClient, test_user: User, auth_headers: dict):
        """Test getting current user information."""
        response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["id"] == str(test_user.id)
    
    async def test_get_current_user_unauthorized(self, async_client: AsyncClient):
        """Test getting current user without authentication."""
        response = await async_client.get("/api/v1/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_refresh_token(self, async_client: AsyncClient, auth_headers: dict):
        """Test token refresh."""
        response = await async_client.post("/api/v1/auth/refresh", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_logout(self, async_client: AsyncClient, auth_headers: dict):
        """Test user logout."""
        response = await async_client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Successfully logged out" in data["message"]
    
    async def test_verify_token_valid(self, async_client: AsyncClient, auth_headers: dict):
        """Test token verification with valid token."""
        response = await async_client.post("/api/v1/auth/verify-token", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is True
        assert "user_id" in data
    
    async def test_verify_token_invalid(self, async_client: AsyncClient):
        """Test token verification with invalid token."""
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = await async_client.post("/api/v1/auth/verify-token", headers=invalid_headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.parametrize("invalid_data", [
        {"email": "invalid-email", "password": "password123", "full_name": "Test"},
        {"email": "test@example.com", "password": "short", "full_name": "Test"},
        {"email": "test@example.com", "password": "password123", "full_name": "A"},
        {"password": "password123", "full_name": "Test"},  # Missing email
    ])
    async def test_register_invalid_data(self, async_client: AsyncClient, invalid_data: dict):
        """Test registration with invalid data."""
        response = await async_client.post("/api/v1/auth/register", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
