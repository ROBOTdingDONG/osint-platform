"""
Database connection and configuration
MongoDB, Redis, and InfluxDB connectivity
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import redis.asyncio as redis
from beanie import init_beanie
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from typing import Optional
import logging

from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization
from app.models.data_source import DataSource
from app.models.collected_data import CollectedData
from app.models.report import Report
from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.models.api_key import APIKey


logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manage database connections and operations
    """
    
    def __init__(self):
        self.mongodb_client: Optional[AsyncIOMotorClient] = None
        self.mongodb_database: Optional[AsyncIOMotorDatabase] = None
        self.redis_client: Optional[redis.Redis] = None
        self.influxdb_client: Optional[InfluxDBClientAsync] = None
    
    async def connect_mongodb(self) -> None:
        """
        Connect to MongoDB and initialize Beanie ODM
        """
        try:
            self.mongodb_client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000
            )
            
            # Test connection
            await self.mongodb_client.admin.command('ping')
            logger.info("✅ Connected to MongoDB")
            
            # Get database
            db_name = (
                settings.MONGODB_TEST_DATABASE 
                if settings.ENVIRONMENT == "test" 
                else settings.MONGODB_DATABASE
            )
            self.mongodb_database = self.mongodb_client[db_name]
            
            # Initialize Beanie with document models
            await init_beanie(
                database=self.mongodb_database,
                document_models=[
                    User,
                    Organization,
                    DataSource,
                    CollectedData,
                    Report,
                    Alert,
                    AuditLog,
                    APIKey,
                ]
            )
            logger.info("✅ Initialized Beanie ODM")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    async def connect_redis(self) -> None:
        """
        Connect to Redis for caching and sessions
        """
        try:
            redis_url = settings.REDIS_URL
            if settings.REDIS_PASSWORD:
                redis_url = redis_url.replace(
                    "redis://", 
                    f"redis://:{settings.REDIS_PASSWORD}@"
                )
            
            self.redis_client = redis.from_url(
                redis_url,
                db=settings.REDIS_DB,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Connected to Redis")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    async def connect_influxdb(self) -> None:
        """
        Connect to InfluxDB for time series data
        """
        try:
            if settings.INFLUXDB_TOKEN:
                self.influxdb_client = InfluxDBClientAsync(
                    url=settings.INFLUXDB_URL,
                    token=settings.INFLUXDB_TOKEN,
                    org=settings.INFLUXDB_ORG
                )
                
                # Test connection
                health = await self.influxdb_client.health()
                if health.status == "pass":
                    logger.info("✅ Connected to InfluxDB")
                else:
                    logger.warning("⚠️ InfluxDB health check failed")
            else:
                logger.info("ℹ️ InfluxDB token not provided, skipping connection")
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to InfluxDB: {e}")
            # Don't raise for InfluxDB as it's not critical for basic functionality
    
    async def disconnect_all(self) -> None:
        """
        Disconnect from all databases
        """
        try:
            if self.mongodb_client:
                self.mongodb_client.close()
                logger.info("✅ Disconnected from MongoDB")
            
            if self.redis_client:
                await self.redis_client.close()
                logger.info("✅ Disconnected from Redis")
            
            if self.influxdb_client:
                await self.influxdb_client.close()
                logger.info("✅ Disconnected from InfluxDB")
                
        except Exception as e:
            logger.error(f"❌ Error during database disconnection: {e}")
    
    async def get_mongodb_database(self) -> AsyncIOMotorDatabase:
        """
        Get MongoDB database instance
        
        Returns:
            MongoDB database instance
        """
        if not self.mongodb_database:
            await self.connect_mongodb()
        return self.mongodb_database
    
    async def get_redis_client(self) -> redis.Redis:
        """
        Get Redis client instance
        
        Returns:
            Redis client instance
        """
        if not self.redis_client:
            await self.connect_redis()
        return self.redis_client
    
    async def get_influxdb_client(self) -> Optional[InfluxDBClientAsync]:
        """
        Get InfluxDB client instance
        
        Returns:
            InfluxDB client instance or None
        """
        if not self.influxdb_client:
            await self.connect_influxdb()
        return self.influxdb_client


# Global database manager instance
db_manager = DatabaseManager()


# Connection functions for FastAPI lifespan
async def connect_to_mongo() -> None:
    """
    Connect to MongoDB on application startup
    """
    await db_manager.connect_mongodb()
    await db_manager.connect_redis()
    await db_manager.connect_influxdb()


async def close_mongo_connection() -> None:
    """
    Close database connections on application shutdown
    """
    await db_manager.disconnect_all()


# Dependency functions
async def get_database() -> AsyncIOMotorDatabase:
    """
    Dependency to get MongoDB database
    """
    return await db_manager.get_mongodb_database()


async def get_redis() -> redis.Redis:
    """
    Dependency to get Redis client
    """
    return await db_manager.get_redis_client()


async def get_influxdb() -> Optional[InfluxDBClientAsync]:
    """
    Dependency to get InfluxDB client
    """
    return await db_manager.get_influxdb_client()


# Cache utilities
class CacheManager:
    """
    Redis cache management utilities
    """
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def get_redis(self) -> redis.Redis:
        if not self.redis:
            self.redis = await get_redis()
        return self.redis
    
    async def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """
        Set a cache value with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        try:
            redis_client = await self.get_redis()
            return await redis_client.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """
        Get a cache value
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        try:
            redis_client = await self.get_redis()
            return await redis_client.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """
        Delete a cache value
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        try:
            redis_client = await self.get_redis()
            return bool(await redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1, ttl: int = 3600) -> int:
        """
        Increment a cache value (useful for rate limiting)
        
        Args:
            key: Cache key
            amount: Amount to increment
            ttl: Time to live in seconds
            
        Returns:
            New value after increment
        """
        try:
            redis_client = await self.get_redis()
            pipe = redis_client.pipeline()
            pipe.incr(key, amount)
            pipe.expire(key, ttl)
            results = await pipe.execute()
            return results[0]
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return 0
    
    async def set_hash(self, key: str, mapping: dict, ttl: int = 3600) -> bool:
        """
        Set a hash in cache
        
        Args:
            key: Cache key
            mapping: Dictionary to store
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        try:
            redis_client = await self.get_redis()
            pipe = redis_client.pipeline()
            pipe.hset(key, mapping=mapping)
            pipe.expire(key, ttl)
            await pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Cache set hash error: {e}")
            return False
    
    async def get_hash(self, key: str) -> Optional[dict]:
        """
        Get a hash from cache
        
        Args:
            key: Cache key
            
        Returns:
            Dictionary or None
        """
        try:
            redis_client = await self.get_redis()
            return await redis_client.hgetall(key)
        except Exception as e:
            logger.error(f"Cache get hash error: {e}")
            return None


# Global cache manager
cache = CacheManager()


# Session management
class SessionManager:
    """
    User session management using Redis
    """
    
    def __init__(self):
        self.cache = cache
        self.session_prefix = "session:"
        self.session_ttl = 86400  # 24 hours
    
    async def create_session(self, user_id: str, session_data: dict) -> str:
        """
        Create a new user session
        
        Args:
            user_id: User ID
            session_data: Session data to store
            
        Returns:
            Session ID
        """
        import uuid
        session_id = str(uuid.uuid4())
        session_key = f"{self.session_prefix}{session_id}"
        
        session_data.update({
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "session_id": session_id
        })
        
        await self.cache.set_hash(session_key, session_data, self.session_ttl)
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """
        Get session data
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None
        """
        session_key = f"{self.session_prefix}{session_id}"
        return await self.cache.get_hash(session_key)
    
    async def update_session(self, session_id: str, session_data: dict) -> bool:
        """
        Update session data
        
        Args:
            session_id: Session ID
            session_data: Updated session data
            
        Returns:
            True if successful
        """
        session_key = f"{self.session_prefix}{session_id}"
        return await self.cache.set_hash(session_key, session_data, self.session_ttl)
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful
        """
        session_key = f"{self.session_prefix}{session_id}"
        return await self.cache.delete(session_key)
    
    async def delete_user_sessions(self, user_id: str) -> int:
        """
        Delete all sessions for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions deleted
        """
        try:
            redis_client = await self.cache.get_redis()
            pattern = f"{self.session_prefix}*"
            deleted = 0
            
            async for key in redis_client.scan_iter(match=pattern):
                session_data = await redis_client.hgetall(key)
                if session_data.get("user_id") == user_id:
                    await redis_client.delete(key)
                    deleted += 1
            
            return deleted
        except Exception as e:
            logger.error(f"Delete user sessions error: {e}")
            return 0


# Global session manager
sessions = SessionManager()