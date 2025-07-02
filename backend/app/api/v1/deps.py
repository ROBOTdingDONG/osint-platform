"""
API dependencies for authentication and authorization
Provides reusable dependency functions for FastAPI endpoints
"""

from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from bson import ObjectId

from app.core.config import settings
from app.core.database import get_collection
from app.core.logging_config import get_logger
from app.db.models.user import User

logger = get_logger('auth.deps')
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Extract user ID from token
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("Token missing user ID")
            raise credentials_exception
            
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise credentials_exception
    
    # Get user from database
    try:
        users_collection = await get_collection("users")
        user_data = await users_collection.find_one({"_id": ObjectId(user_id)})
        
        if user_data is None:
            logger.warning(f"User not found: {user_id}")
            raise credentials_exception
        
        user = User(**user_data)
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user account"
            )
        
        return user
        
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {e}")
        raise credentials_exception


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependency to get current active user
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependency to get current verified user
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        User: Current verified user
        
    Raises:
        HTTPException: If user is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return current_user


async def get_admin_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependency to get current admin user
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        User: Current admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_premium_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependency to get current premium user
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        User: Current premium user
        
    Raises:
        HTTPException: If user doesn't have premium access
    """
    if current_user.role not in ["premium", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required"
        )
    return current_user


class RateLimitDependency:
    """Rate limiting dependency"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_times = {}
    
    async def __call__(self, current_user: Annotated[User, Depends(get_current_user)]):
        """Check rate limit for current user"""
        import time
        
        user_id = str(current_user.id)
        current_time = time.time()
        
        # Clean old requests (older than 1 minute)
        if user_id in self.request_times:
            self.request_times[user_id] = [
                t for t in self.request_times[user_id] 
                if current_time - t < 60
            ]
        else:
            self.request_times[user_id] = []
        
        # Check rate limit
        if len(self.request_times[user_id]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Add current request
        self.request_times[user_id].append(current_time)
        
        return current_user


# Rate limiting instances
standard_rate_limit = RateLimitDependency(requests_per_minute=60)
strict_rate_limit = RateLimitDependency(requests_per_minute=10)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User | None:
    """
    Optional dependency to get current user (doesn't raise if no token)
    
    Args:
        credentials: HTTP Bearer token credentials (optional)
        
    Returns:
        User | None: Current user if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


# Common dependency combinations
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentVerifiedUser = Annotated[User, Depends(get_current_verified_user)]
AdminUser = Annotated[User, Depends(get_admin_user)]
PremiumUser = Annotated[User, Depends(get_premium_user)]
RateLimitedUser = Annotated[User, Depends(standard_rate_limit)]
StrictRateLimitedUser = Annotated[User, Depends(strict_rate_limit)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]