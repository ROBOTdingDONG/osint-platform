"""
Pytest configuration and fixtures for OSINT Platform backend tests
Provides reusable test fixtures and setup
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.database import get_database, mongodb_client
from app.db.models.user import User
from app.api.v1.endpoints.auth import get_password_hash, create_access_token

# Test database configuration
TEST_DATABASE_NAME = "osint_platform_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db() -> AsyncGenerator[AsyncIOMotorClient, None]:
    """Create a test database connection."""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    # Ensure we're using the test database
    db = client[TEST_DATABASE_NAME]
    
    # Clean up any existing test data
    await db.drop_collection("users")
    await db.drop_collection("collected_data")
    await db.drop_collection("data_sources")
    await db.drop_collection("analysis_results")
    await db.drop_collection("reports")
    await db.drop_collection("alerts")
    
    yield client
    
    # Cleanup after tests
    await client.drop_database(TEST_DATABASE_NAME)
    client.close()


@pytest.fixture
async def override_get_database(test_db: AsyncIOMotorClient):
    """Override the get_database dependency for tests."""
    async def _get_test_database():
        return test_db[TEST_DATABASE_NAME]
    
    app.dependency_overrides[get_database] = _get_test_database
    yield
    del app.dependency_overrides[get_database]


@pytest.fixture
async def async_client(override_get_database) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sync_client(override_get_database) -> Generator[TestClient, None, None]:
    """Create a synchronous HTTP client for testing."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def test_user(test_db: AsyncIOMotorClient) -> User:
    """Create a test user."""
    db = test_db[TEST_DATABASE_NAME]
    users_collection = db.users
    
    user_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "company": "Test Company",
        "password_hash": get_password_hash("testpassword123"),
        "is_active": True,
        "is_verified": True,
        "role": "user"
    }
    
    result = await users_collection.insert_one(user_data)
    user_data["_id"] = result.inserted_id
    
    return User(**user_data)


@pytest.fixture
async def admin_user(test_db: AsyncIOMotorClient) -> User:
    """Create a test admin user."""
    db = test_db[TEST_DATABASE_NAME]
    users_collection = db.users
    
    user_data = {
        "email": "admin@example.com",
        "full_name": "Admin User",
        "company": "Test Company",
        "password_hash": get_password_hash("adminpassword123"),
        "is_active": True,
        "is_verified": True,
        "role": "admin"
    }
    
    result = await users_collection.insert_one(user_data)
    user_data["_id"] = result.inserted_id
    
    return User(**user_data)


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authentication headers for test user."""
    access_token = create_access_token(
        data={"sub": str(test_user.id), "email": test_user.email}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(admin_user: User) -> dict:
    """Create authentication headers for admin user."""
    access_token = create_access_token(
        data={"sub": str(admin_user.id), "email": admin_user.email}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_tweet_data() -> dict:
    """Sample tweet data for testing."""
    return {
        "id": "1234567890",
        "text": "This is a sample tweet for testing purposes #test",
        "author": {
            "id": "987654321",
            "username": "testuser",
            "name": "Test User",
            "followers_count": 1000,
            "verified": False
        },
        "created_at": "2024-01-15T10:00:00Z",
        "metrics": {
            "retweet_count": 10,
            "favorite_count": 25,
            "reply_count": 5
        },
        "metadata": {
            "source": "twitter",
            "keyword": "test",
            "language": "en",
            "hashtags": ["test"],
            "mentions": [],
            "urls": []
        }
    }


@pytest.fixture
def sample_news_data() -> dict:
    """Sample news article data for testing."""
    return {
        "id": "news_123",
        "title": "Test News Article",
        "content": "This is a test news article content for testing purposes.",
        "author": "Test Journalist",
        "published_at": "2024-01-15T10:00:00Z",
        "source": {
            "name": "Test News Source",
            "url": "https://testnews.com"
        },
        "metadata": {
            "source": "news",
            "category": "technology",
            "language": "en",
            "url": "https://testnews.com/article/123"
        }
    }


class TestSettings:
    """Test-specific settings override."""
    ENVIRONMENT = "testing"
    MONGODB_DATABASE = TEST_DATABASE_NAME
    JWT_SECRET = "test-secret-key"
    LOG_LEVEL = "DEBUG"


@pytest.fixture(autouse=True)
def override_settings():
    """Override settings for testing."""
    # Store original values
    original_env = settings.ENVIRONMENT
    original_db = settings.MONGODB_DATABASE
    original_secret = settings.JWT_SECRET
    
    # Set test values
    settings.ENVIRONMENT = "testing"
    settings.MONGODB_DATABASE = TEST_DATABASE_NAME
    settings.JWT_SECRET = "test-secret-key"
    
    yield
    
    # Restore original values
    settings.ENVIRONMENT = original_env
    settings.MONGODB_DATABASE = original_db
    settings.JWT_SECRET = original_secret
