"""
Main FastAPI application for OSINT Platform
Provides REST API endpoints for data collection, analysis, and reporting
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
import logging
from datetime import datetime

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.logging_config import setup_logging
from app.api.v1.router import api_router


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting OSINT Platform API...")
    await connect_to_mongo()
    logger.info("✅ Database connected successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down OSINT Platform API...")
    await close_mongo_connection()
    logger.info("✅ Database connection closed")


# Create FastAPI application
app = FastAPI(
    title="OSINT Platform API",
    description="Enterprise-grade Open Source Intelligence platform for automated competitive intelligence and market research",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan,
    servers=[
        {
            "url": settings.API_URL,
            "description": f"{settings.ENVIRONMENT.title()} server"
        }
    ]
)

# Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.ALLOWED_HOSTS
)


# Health Check Endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """Detailed health check with system information"""
    from app.core.database import get_database
    
    try:
        # Test database connection
        db = await get_database()
        await db.command("ping")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "services": {
            "database": db_status,
            "api": "healthy"
        }
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to OSINT Platform API",
        "version": "1.0.0",
        "documentation": f"{settings.API_URL}/docs",
        "health": f"{settings.API_URL}/health"
    }


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error occurred"
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )