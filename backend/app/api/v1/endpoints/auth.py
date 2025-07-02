"""
Authentication endpoints for OSINT Platform
Handles user login, registration, and token management
"""

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_collection
from app.core.logging_config import get_logger, security_logger
from app.db.models.user import User, UserCreate, UserLogin
from app.api.v1.deps import get_current_user

logger = get_logger('auth')
router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Response models
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    company: str = Field(None, max_length=100)


# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


async def authenticate_user(email: str, password: str) -> User | None:
    """Authenticate user with email and password"""
    try:
        users_collection = await get_collection("users")
        user_data = await users_collection.find_one({"email": email})
        
        if not user_data:
            security_logger.log_auth_failure(email, "User not found")
            return None
        
        user = User(**user_data)
        
        if not user.is_active:
            security_logger.log_auth_failure(email, "Account disabled")
            return None
        
        if not verify_password(password, user.password_hash):
            security_logger.log_auth_failure(email, "Invalid password")
            return None
        
        security_logger.log_auth_attempt(email, True)
        return user
        
    except Exception as e:
        logger.error(f"Authentication error for {email}: {e}")
        return None


# Authentication endpoints
@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """Authenticate user and return access token"""
    
    user = await authenticate_user(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    try:
        users_collection = await get_collection("users")
        await users_collection.update_one(
            {"_id": user.id},
            {"$set": {"last_login": datetime.utcnow()}}
        )
    except Exception as e:
        logger.warning(f"Failed to update last login for user {user.id}: {e}")
    
    # Create access token
    access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    
    logger.info(f"User {user.email} logged in successfully")
    
    return TokenResponse(
        access_token=access_token,
        expires_in=int(access_token_expires.total_seconds()),
        user_id=str(user.id)
    )


@router.post("/register", response_model=TokenResponse)
async def register(register_data: RegisterRequest):
    """Register new user account"""
    
    try:
        users_collection = await get_collection("users")
        
        # Check if user already exists
        existing_user = await users_collection.find_one({"email": register_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        password_hash = get_password_hash(register_data.password)
        
        user_data = {
            "email": register_data.email,
            "full_name": register_data.full_name,
            "company": register_data.company,
            "password_hash": password_hash,
            "is_active": True,
            "is_verified": False,
            "role": "user",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await users_collection.insert_one(user_data)
        user_id = result.inserted_id
        
        # Create access token
        access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        access_token = create_access_token(
            data={"sub": str(user_id), "email": register_data.email},
            expires_delta=access_token_expires
        )
        
        logger.info(f"New user registered: {register_data.email}")
        
        return TokenResponse(
            access_token=access_token,
            expires_in=int(access_token_expires.total_seconds()),
            user_id=str(user_id)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error for {register_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/refresh")
async def refresh_token(current_user: Annotated[User, Depends(get_current_user)]):
    """Refresh access token"""
    
    access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    access_token = create_access_token(
        data={"sub": str(current_user.id), "email": current_user.email},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=int(access_token_expires.total_seconds()),
        user_id=str(current_user.id)
    )


@router.post("/logout")
async def logout(current_user: Annotated[User, Depends(get_current_user)]):
    """Logout user (client-side token invalidation)"""
    
    logger.info(f"User {current_user.email} logged out")
    
    return {
        "message": "Successfully logged out",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/me")
async def get_current_user_info(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current user information"""
    
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "company": current_user.company,
        "role": current_user.role,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at.isoformat(),
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }


@router.post("/verify-token")
async def verify_token(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    """Verify if token is valid"""
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return {
            "valid": True,
            "user_id": user_id,
            "expires": payload.get("exp")
        }
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )