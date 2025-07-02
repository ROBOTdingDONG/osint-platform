"""
Database connection and management for MongoDB
Handles async database operations using Motor driver
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global database variables
mongodb_client: Optional[AsyncIOMotorClient] = None
mongodb_database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo() -> None:
    """Create database connection pool"""
    global mongodb_client, mongodb_database
    
    try:
        logger.info("Connecting to MongoDB...")
        logger.info(f"MongoDB URL: {settings.MONGODB_URL.split('@')[0]}@***")
        
        # Create MongoDB client with connection pool
        mongodb_client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=10,
            minPoolSize=1,
            maxIdleTimeMS=45000,
            connectTimeoutMS=10000,
            serverSelectionTimeoutMS=10000,
            socketTimeoutMS=20000,
            heartbeatFrequencyMS=10000
        )
        
        # Get database
        mongodb_database = mongodb_client[settings.MONGODB_DATABASE]
        
        # Test connection
        await mongodb_client.admin.command('ping')
        
        logger.info(f"✅ Connected to MongoDB database: {settings.MONGODB_DATABASE}")
        
        # Create indexes
        await create_indexes()
        
    except ServerSelectionTimeoutError:
        logger.error("❌ Failed to connect to MongoDB: Server selection timeout")
        raise
    except ConnectionFailure as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error connecting to MongoDB: {e}")
        raise


async def close_mongo_connection() -> None:
    """Close database connection"""
    global mongodb_client
    
    if mongodb_client:
        logger.info("Closing MongoDB connection...")
        mongodb_client.close()
        logger.info("✅ MongoDB connection closed")


async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if mongodb_database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return mongodb_database


async def get_collection(collection_name: str):
    """Get a specific collection"""
    database = await get_database()
    return database[collection_name]


async def create_indexes() -> None:
    """Create database indexes for optimal performance"""
    try:
        database = await get_database()
        
        logger.info("Creating database indexes...")
        
        # Users collection indexes
        users_collection = database.users
        await users_collection.create_index("email", unique=True)
        await users_collection.create_index("username", unique=True)
        await users_collection.create_index("created_at")
        
        # Data sources collection indexes
        sources_collection = database.data_sources
        await sources_collection.create_index([("source_type", 1), ("url", 1)], unique=True)
        await sources_collection.create_index("created_at")
        await sources_collection.create_index("is_active")
        
        # Collected data indexes
        data_collection = database.collected_data
        await data_collection.create_index([("source_id", 1), ("collected_at", -1)])
        await data_collection.create_index("content_hash", unique=True)
        await data_collection.create_index("collected_at")
        await data_collection.create_index("sentiment_score")
        
        # Analysis results indexes
        analysis_collection = database.analysis_results
        await analysis_collection.create_index([("data_id", 1), ("analysis_type", 1)])
        await analysis_collection.create_index("created_at")
        await analysis_collection.create_index("confidence_score")
        
        # Reports collection indexes
        reports_collection = database.reports
        await reports_collection.create_index("user_id")
        await reports_collection.create_index("created_at")
        await reports_collection.create_index("report_type")
        
        # Alerts collection indexes
        alerts_collection = database.alerts
        await alerts_collection.create_index([("user_id", 1), ("is_read", 1)])
        await alerts_collection.create_index("created_at")
        await alerts_collection.create_index("alert_type")
        await alerts_collection.create_index("priority")
        
        # API keys collection indexes
        api_keys_collection = database.api_keys
        await api_keys_collection.create_index("key_hash", unique=True)
        await api_keys_collection.create_index("user_id")
        await api_keys_collection.create_index("expires_at")
        
        logger.info("✅ Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"❌ Error creating database indexes: {e}")
        # Don't raise here as indexes are not critical for startup


async def check_database_health() -> dict:
    """Check database health and return status"""
    try:
        database = await get_database()
        
        # Test basic operations
        await database.command("ping")
        
        # Get database stats
        stats = await database.command("dbStats")
        
        # Count collections
        collections = await database.list_collection_names()
        
        return {
            "status": "healthy",
            "database": settings.MONGODB_DATABASE,
            "collections_count": len(collections),
            "data_size": stats.get("dataSize", 0),
            "storage_size": stats.get("storageSize", 0),
            "indexes": stats.get("indexes", 0)
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Database transaction helper
async def run_in_transaction(operations, session=None):
    """Execute multiple operations in a transaction"""
    client = mongodb_client
    if not client:
        raise RuntimeError("Database client not initialized")
    
    if session is None:
        async with await client.start_session() as session:
            async with session.start_transaction():
                result = await operations(session)
                return result
    else:
        async with session.start_transaction():
            result = await operations(session)
            return result


# Utility functions
async def ensure_unique_index(collection_name: str, field: str, unique: bool = True):
    """Ensure an index exists on a collection"""
    try:
        collection = await get_collection(collection_name)
        await collection.create_index(field, unique=unique)
        logger.info(f"Index created on {collection_name}.{field}")
    except Exception as e:
        logger.warning(f"Could not create index on {collection_name}.{field}: {e}")


async def drop_collection_if_exists(collection_name: str):
    """Drop a collection if it exists (useful for testing)"""
    try:
        database = await get_database()
        collections = await database.list_collection_names()
        if collection_name in collections:
            await database.drop_collection(collection_name)
            logger.info(f"Dropped collection: {collection_name}")
    except Exception as e:
        logger.error(f"Error dropping collection {collection_name}: {e}")


# Export commonly used functions
__all__ = [
    'connect_to_mongo',
    'close_mongo_connection', 
    'get_database',
    'get_collection',
    'check_database_health',
    'run_in_transaction'
]