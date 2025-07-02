"""
User management endpoints for OSINT Platform
Handles user CRUD operations and profile management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.api.v1.deps import CurrentUser, AdminUser
from app.core.logging_config import get_logger

logger = get_logger('users')
router = APIRouter()


@router.get("/profile")
async def get_user_profile(current_user: CurrentUser):
    """Get current user profile"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "company": current_user.company,
        "role": current_user.role
    }


@router.get("/")
async def list_users(admin_user: AdminUser):
    """List all users (admin only)"""
    return {"message": "User list endpoint - coming soon"}
