"""
Configuration settings for the OSINT Platform
Manages environment variables and application settings
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Application Settings
    APP_NAME: str = "OSINT Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # API Settings
    API_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Security Settings
    JWT_SECRET: str = "your-super-secret-jwt-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    ENCRYPTION_KEY: Optional[str] = None
    
    # Database Settings
    MONGODB_URL: str = "mongodb://admin:password@localhost:27017/osint_platform?authSource=admin"
    MONGODB_DATABASE: str = "osint_platform"
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # External API Keys
    OPENAI_API_KEY: Optional[str] = None
    TWITTER_API_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # Email Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@osintplatform.com"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080"
    ]
    
    # Security
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 10
    
    # AWS Settings
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: Optional[str] = None
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def validate_cors_origins(cls, v):
        """Validate and parse CORS origins"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @field_validator('ALLOWED_HOSTS', mode='before')
    @classmethod
    def validate_allowed_hosts(cls, v):
        """Validate and parse allowed hosts"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(',')]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()


# Configuration validation
def validate_config():
    """Validate critical configuration settings"""
    errors = []
    
    # Check required API keys for production
    if settings.ENVIRONMENT == "production":
        if not settings.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required for production")
        
        if not settings.JWT_SECRET or settings.JWT_SECRET == "your-super-secret-jwt-key":
            errors.append("JWT_SECRET must be set to a secure value in production")
        
        if not settings.ENCRYPTION_KEY:
            errors.append("ENCRYPTION_KEY is required for production")
    
    # Check database configuration
    if not settings.MONGODB_URL:
        errors.append("MONGODB_URL is required")
    
    if errors:
        raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
    
    return True


# Environment-specific configurations
class DevelopmentConfig(Settings):
    """Development environment configuration"""
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"


class ProductionConfig(Settings):
    """Production environment configuration"""
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    ALLOWED_HOSTS: List[str] = ["osintplatform.com", "api.osintplatform.com"]


class TestingConfig(Settings):
    """Testing environment configuration"""
    ENVIRONMENT: str = "testing"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    MONGODB_DATABASE: str = "osint_platform_test"


def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()


# Export settings instance
settings = get_settings()

# Validate configuration on import
validate_config()