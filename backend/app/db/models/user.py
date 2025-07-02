"""
User models for OSINT Platform
Defines user data structures and validation schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    
    class Config:
        json_encoders = {ObjectId: str}


class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one digit
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        
        # Check for at least one letter
        if not any(char.isalpha() for char in v):
            raise ValueError('Password must contain at least one letter')
        
        return v


class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """User update model"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    
    class Config:
        json_encoders = {ObjectId: str}


class UserPasswordUpdate(BaseModel):
    """User password update model"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        
        if not any(char.isalpha() for char in v):
            raise ValueError('Password must contain at least one letter')
        
        return v


class User(UserBase):
    """Full user model with all fields"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    password_hash: str
    is_active: bool = True
    is_verified: bool = False
    role: str = Field(default="user")  # user, premium, admin
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # Profile information
    avatar_url: Optional[str] = None
    timezone: str = Field(default="UTC")
    
    # Subscription information
    subscription_plan: str = Field(default="free")  # free, basic, premium, enterprise
    subscription_expires: Optional[datetime] = None
    
    # API usage tracking
    api_calls_used: int = Field(default=0)
    api_calls_limit: int = Field(default=1000)  # Monthly limit
    
    # User preferences
    notifications_enabled: bool = True
    email_notifications: bool = True
    
    # Security
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = None
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UserInDB(User):
    """User model as stored in database"""
    pass


class UserResponse(BaseModel):
    """User response model (without sensitive data)"""
    id: str
    email: EmailStr
    full_name: str
    company: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    avatar_url: Optional[str]
    timezone: str
    subscription_plan: str
    subscription_expires: Optional[datetime]
    api_calls_used: int
    api_calls_limit: int
    notifications_enabled: bool
    
    class Config:
        json_encoders = {ObjectId: str}


class UserListResponse(BaseModel):
    """User list response model"""
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class UserStats(BaseModel):
    """User statistics model"""
    total_users: int
    active_users: int
    verified_users: int
    premium_users: int
    new_users_this_month: int
    
    # Role breakdown
    role_breakdown: dict = Field(default_factory=dict)
    
    # Subscription breakdown
    subscription_breakdown: dict = Field(default_factory=dict)


class APIKeyCreate(BaseModel):
    """API key creation model"""
    name: str = Field(..., min_length=1, max_length=100)
    permissions: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None


class APIKey(BaseModel):
    """API key model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    name: str
    key_hash: str  # Hashed version of the key
    key_preview: str  # Last 4 characters for display
    permissions: List[str] = Field(default_factory=list)
    is_active: bool = True
    
    # Usage tracking
    last_used: Optional[datetime] = None
    total_requests: int = Field(default=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class APIKeyResponse(BaseModel):
    """API key response model"""
    id: str
    name: str
    key_preview: str
    permissions: List[str]
    is_active: bool
    last_used: Optional[datetime]
    total_requests: int
    created_at: datetime
    expires_at: Optional[datetime]


# Export models
__all__ = [
    'User',
    'UserCreate', 
    'UserLogin',
    'UserUpdate',
    'UserPasswordUpdate',
    'UserResponse',
    'UserListResponse',
    'UserStats',
    'APIKey',
    'APIKeyCreate',
    'APIKeyResponse',
    'PyObjectId'
]