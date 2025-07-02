"""
User data models and schemas
Pydantic models for user-related data structures
"""

from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """
    Available user roles in the system
    """
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API_USER = "api_user"


class UserStatus(str, Enum):
    """
    User account status
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class MFAMethod(str, Enum):
    """
    Multi-factor authentication methods
    """
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"


class UserPreferences(BaseModel):
    """
    User preferences and settings
    """
    timezone: str = "UTC"
    language: str = "en"
    theme: str = "light"
    email_notifications: bool = True
    push_notifications: bool = True
    weekly_digest: bool = True
    data_retention_days: int = 365
    default_dashboard: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "timezone": "America/New_York",
                "language": "en",
                "theme": "dark",
                "email_notifications": True,
                "push_notifications": False,
                "weekly_digest": True,
                "data_retention_days": 365,
                "default_dashboard": "overview"
            }
        }


class UserMFA(BaseModel):
    """
    Multi-factor authentication settings
    """
    enabled: bool = False
    method: Optional[MFAMethod] = None
    secret: Optional[str] = None
    backup_codes: List[str] = []
    last_used: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "enabled": True,
                "method": "totp",
                "backup_codes": ["123456", "789012"],
                "last_used": "2025-07-02T10:30:00Z"
            }
        }


class UserActivity(BaseModel):
    """
    User activity tracking
    """
    last_login: Optional[datetime] = None
    last_active: Optional[datetime] = None
    login_count: int = 0
    failed_login_attempts: int = 0
    last_failed_login: Optional[datetime] = None
    ip_addresses: List[str] = []
    user_agents: List[str] = []
    
    class Config:
        schema_extra = {
            "example": {
                "last_login": "2025-07-02T10:30:00Z",
                "last_active": "2025-07-02T11:30:00Z",
                "login_count": 42,
                "failed_login_attempts": 0,
                "ip_addresses": ["192.168.1.1", "10.0.0.1"],
                "user_agents": ["Mozilla/5.0..."]
            }
        }


class User(Document):
    """
    User document model for MongoDB
    """
    # Basic Information
    email: Indexed(EmailStr, unique=True)
    full_name: str
    password_hash: str
    
    # Role and Permissions
    role: UserRole = UserRole.VIEWER
    permissions: List[str] = []
    custom_permissions: List[str] = []
    
    # Organization
    organization_id: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    
    # Account Status
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    is_email_verified: bool = False
    email_verification_token: Optional[str] = None
    
    # Security
    mfa: UserMFA = UserMFA()
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    
    # Preferences
    preferences: UserPreferences = UserPreferences()
    
    # Activity
    activity: UserActivity = UserActivity()
    
    # Avatar and Profile
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = {}
    
    class Settings:
        collection = "users"
        indexes = [
            "email",
            "organization_id",
            "role",
            "status",
            "created_at",
            [("email", 1), ("organization_id", 1)],
        ]
    
    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "role": "analyst",
                "organization_id": "org_123456",
                "department": "Security",
                "job_title": "Senior Analyst",
                "status": "active",
                "is_email_verified": True
            }
        }


# API Schemas
class UserCreate(BaseModel):
    """
    Schema for user creation
    """
    email: EmailStr
    full_name: str
    password: str
    organization: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    
    @validator("password")
    def validate_password(cls, v):
        from app.core.security import security_manager
        validation = security_manager.validate_password_strength(v)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["feedback"]))
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "password": "SecurePassword123!",
                "organization": "ACME Corp",
                "department": "Security",
                "job_title": "Senior Analyst"
            }
        }


class UserLogin(BaseModel):
    """
    Schema for user login
    """
    email: EmailStr
    password: str
    remember_me: bool = False
    
    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "password": "SecurePassword123!",
                "remember_me": True
            }
        }


class UserUpdate(BaseModel):
    """
    Schema for user updates
    """
    full_name: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    bio: Optional[str] = None
    preferences: Optional[UserPreferences] = None
    
    class Config:
        schema_extra = {
            "example": {
                "full_name": "John Smith",
                "department": "Cybersecurity",
                "job_title": "Lead Analyst",
                "bio": "Cybersecurity professional with 10+ years experience"
            }
        }


class UserResponse(BaseModel):
    """
    Schema for user API responses
    """
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    organization_id: Optional[str]
    department: Optional[str]
    job_title: Optional[str]
    status: UserStatus
    is_email_verified: bool
    avatar_url: Optional[str]
    bio: Optional[str]
    preferences: UserPreferences
    activity: UserActivity
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "user_123456",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "role": "analyst",
                "organization_id": "org_123456",
                "department": "Security",
                "job_title": "Senior Analyst",
                "status": "active",
                "is_email_verified": True,
                "created_at": "2025-07-02T10:30:00Z",
                "updated_at": "2025-07-02T10:30:00Z"
            }
        }


class TokenResponse(BaseModel):
    """
    Schema for authentication token response
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": "user_123456",
                    "email": "john.doe@example.com",
                    "full_name": "John Doe",
                    "role": "analyst"
                }
            }
        }


class PasswordReset(BaseModel):
    """
    Schema for password reset request
    """
    email: EmailStr
    
    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@example.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """
    Schema for password reset confirmation
    """
    token: str
    new_password: str
    
    @validator("new_password")
    def validate_password(cls, v):
        from app.core.security import security_manager
        validation = security_manager.validate_password_strength(v)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["feedback"]))
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "token": "reset_token_123456",
                "new_password": "NewSecurePassword123!"
            }
        }


class EmailVerification(BaseModel):
    """
    Schema for email verification
    """
    token: str
    
    class Config:
        schema_extra = {
            "example": {
                "token": "verification_token_123456"
            }
        }