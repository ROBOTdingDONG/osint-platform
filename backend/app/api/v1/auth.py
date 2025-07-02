"""
Authentication API endpoints
User registration, login, logout, password reset, and MFA
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import logging

from app.models.user import (
    User, UserCreate, UserLogin, UserResponse, TokenResponse,
    PasswordReset, PasswordResetConfirm, EmailVerification,
    UserRole, UserStatus
)
from app.core.security import security_manager, security, get_permissions_for_role
from app.core.config import settings
from app.core.database import sessions
from app.services.email import send_verification_email, send_password_reset_email
from app.services.audit import log_user_action
from app.api.dependencies import get_current_user, RateLimitChecker


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
rate_limiter = RateLimitChecker()


class MFASetup(BaseModel):
    """Schema for MFA setup"""
    method: str = "totp"


class MFAVerify(BaseModel):
    """Schema for MFA verification"""
    mfa_token: str
    code: str


class RefreshToken(BaseModel):
    """Schema for token refresh"""
    refresh_token: str


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    _: bool = Depends(rate_limiter.check_auth_rate_limit)
):
    """
    Register a new user account
    
    - **email**: Valid email address
    - **password**: Strong password meeting requirements
    - **full_name**: User's full name
    - **organization**: Optional organization name
    """
    try:
        # Check if user already exists
        existing_user = await User.find_one(User.email == user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Hash password
        password_hash = security_manager.hash_password(user_data.password)
        
        # Create user
        user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            password_hash=password_hash,
            role=UserRole.VIEWER,  # Default role
            permissions=get_permissions_for_role(UserRole.VIEWER),
            department=user_data.department,
            job_title=user_data.job_title,
            status=UserStatus.PENDING_VERIFICATION
        )
        
        # Generate email verification token
        verification_token = security_manager.create_email_verification_token(user_data.email)
        user.email_verification_token = verification_token
        
        # Save user
        await user.insert()
        
        # Send verification email
        background_tasks.add_task(
            send_verification_email,
            user_data.email,
            user_data.full_name,
            verification_token
        )
        
        # Log action
        background_tasks.add_task(
            log_user_action,
            str(user.id),
            "user_registered",
            {"email": user_data.email, "organization": user_data.organization}
        )
        
        logger.info(f"User registered: {user_data.email}")
        
        return {
            "success": True,
            "message": "Registration successful. Please verify your email.",
            "data": {
                "user_id": str(user.id),
                "email": user_data.email,
                "verification_required": True
            }
        }
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/verify-email", response_model=dict)
async def verify_email(
    verification_data: EmailVerification,
    background_tasks: BackgroundTasks,
    _: bool = Depends(rate_limiter.check_auth_rate_limit)
):
    """
    Verify user email address
    
    - **token**: Email verification token
    """
    try:
        # Verify token
        email = security_manager.verify_email_verification_token(verification_data.token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        # Find user
        user = await User.find_one(User.email == email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_email_verified:
            return {
                "success": True,
                "message": "Email already verified"
            }
        
        # Update user
        user.is_email_verified = True
        user.status = UserStatus.ACTIVE
        user.email_verification_token = None
        user.updated_at = datetime.utcnow()
        await user.save()
        
        # Log action
        background_tasks.add_task(
            log_user_action,
            str(user.id),
            "email_verified",
            {"email": email}
        )
        
        logger.info(f"Email verified: {email}")
        
        return {
            "success": True,
            "message": "Email verified successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    background_tasks: BackgroundTasks,
    _: bool = Depends(rate_limiter.check_auth_rate_limit)
):
    """
    Authenticate user and return access tokens
    
    - **email**: User email address
    - **password**: User password
    - **remember_me**: Extend token lifetime
    """
    try:
        # Find user
        user = await User.find_one(User.email == login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check password
        if not security_manager.verify_password(login_data.password, user.password_hash):
            # Update failed login attempts
            user.activity.failed_login_attempts += 1
            user.activity.last_failed_login = datetime.utcnow()
            await user.save()
            
            # Log failed attempt
            background_tasks.add_task(
                log_user_action,
                str(user.id),
                "login_failed",
                {"email": login_data.email, "reason": "invalid_password"}
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check account status
        if user.status == UserStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account suspended"
            )
        
        if user.status == UserStatus.PENDING_VERIFICATION:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required"
            )
        
        # Check if MFA is enabled
        if user.mfa.enabled:
            # Create temporary MFA token
            mfa_token_data = {
                "user_id": str(user.id),
                "email": user.email,
                "mfa_required": True
            }
            mfa_token = security_manager.create_access_token(
                mfa_token_data,
                expires_delta=timedelta(minutes=5)  # 5 minute expiry
            )
            
            return {
                "success": False,
                "mfa_required": True,
                "mfa_token": mfa_token,
                "message": "MFA verification required"
            }
        
        # Create tokens
        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "permissions": user.permissions + user.custom_permissions
        }
        
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES * (7 if login_data.remember_me else 1)
        )
        refresh_token_expires = timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS * (2 if login_data.remember_me else 1)
        )
        
        access_token = security_manager.create_access_token(
            token_data, access_token_expires
        )
        refresh_token = security_manager.create_refresh_token(
            token_data, refresh_token_expires
        )
        
        # Update user activity
        user.activity.last_login = datetime.utcnow()
        user.activity.last_active = datetime.utcnow()
        user.activity.login_count += 1
        user.activity.failed_login_attempts = 0  # Reset failed attempts
        await user.save()
        
        # Create session
        session_data = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "login_time": datetime.utcnow().isoformat()
        }
        session_id = await sessions.create_session(str(user.id), session_data)
        
        # Log successful login
        background_tasks.add_task(
            log_user_action,
            str(user.id),
            "login_success",
            {"email": login_data.email, "session_id": session_id}
        )
        
        logger.info(f"User logged in: {login_data.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_token_expires.total_seconds()),
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/mfa/verify", response_model=TokenResponse)
async def verify_mfa(
    mfa_data: MFAVerify,
    background_tasks: BackgroundTasks,
    _: bool = Depends(rate_limiter.check_auth_rate_limit)
):
    """
    Verify MFA token and complete authentication
    
    - **mfa_token**: Temporary MFA token from login
    - **code**: TOTP code from authenticator app
    """
    try:
        # Verify MFA token
        token_data = security_manager.verify_token(mfa_data.mfa_token)
        if not token_data.get("mfa_required"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MFA token"
            )
        
        # Find user
        user = await User.find_one(User.id == token_data["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify MFA code
        if not security_manager.verify_mfa_token(user.mfa.secret, mfa_data.code):
            # Log failed MFA attempt
            background_tasks.add_task(
                log_user_action,
                str(user.id),
                "mfa_failed",
                {"email": user.email}
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code"
            )
        
        # Create full access tokens
        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "permissions": user.permissions + user.custom_permissions
        }
        
        access_token = security_manager.create_access_token(token_data)
        refresh_token = security_manager.create_refresh_token(token_data)
        
        # Update MFA usage
        user.mfa.last_used = datetime.utcnow()
        user.activity.last_login = datetime.utcnow()
        user.activity.last_active = datetime.utcnow()
        user.activity.login_count += 1
        await user.save()
        
        # Log successful MFA
        background_tasks.add_task(
            log_user_action,
            str(user.id),
            "mfa_success",
            {"email": user.email}
        )
        
        logger.info(f"MFA verified for user: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA verification failed"
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(
    refresh_data: RefreshToken,
    background_tasks: BackgroundTasks
):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    """
    try:
        # Verify refresh token
        token_data = security_manager.verify_token(refresh_data.refresh_token)
        if token_data.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Find user
        user = await User.find_one(User.id == token_data["user_id"])
        if not user or user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        new_token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "permissions": user.permissions + user.custom_permissions
        }
        
        access_token = security_manager.create_access_token(new_token_data)
        
        # Update last active
        user.activity.last_active = datetime.utcnow()
        await user.save()
        
        # Log token refresh
        background_tasks.add_task(
            log_user_action,
            str(user.id),
            "token_refreshed",
            {"email": user.email}
        )
        
        return {
            "success": True,
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", response_model=dict)
async def logout(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Logout user and invalidate tokens
    """
    try:
        # Delete user sessions
        deleted_sessions = await sessions.delete_user_sessions(str(current_user.id))
        
        # Log logout
        background_tasks.add_task(
            log_user_action,
            str(current_user.id),
            "logout",
            {"email": current_user.email, "sessions_deleted": deleted_sessions}
        )
        
        logger.info(f"User logged out: {current_user.email}")
        
        return {
            "success": True,
            "message": "Logged out successfully"
        }
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/password-reset", response_model=dict)
async def request_password_reset(
    reset_data: PasswordReset,
    background_tasks: BackgroundTasks,
    _: bool = Depends(rate_limiter.check_auth_rate_limit)
):
    """
    Request password reset email
    
    - **email**: User email address
    """
    try:
        # Find user
        user = await User.find_one(User.email == reset_data.email)
        if not user:
            # Don't reveal if email exists
            return {
                "success": True,
                "message": "If the email exists, a password reset link has been sent"
            }
        
        # Generate reset token
        reset_token = security_manager.create_password_reset_token(reset_data.email)
        
        # Update user
        user.password_reset_token = reset_token
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        await user.save()
        
        # Send reset email
        background_tasks.add_task(
            send_password_reset_email,
            reset_data.email,
            user.full_name,
            reset_token
        )
        
        # Log action
        background_tasks.add_task(
            log_user_action,
            str(user.id),
            "password_reset_requested",
            {"email": reset_data.email}
        )
        
        logger.info(f"Password reset requested: {reset_data.email}")
        
        return {
            "success": True,
            "message": "If the email exists, a password reset link has been sent"
        }
        
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )


@router.post("/password-reset/confirm", response_model=dict)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    background_tasks: BackgroundTasks,
    _: bool = Depends(rate_limiter.check_auth_rate_limit)
):
    """
    Confirm password reset with new password
    
    - **token**: Password reset token
    - **new_password**: New password
    """
    try:
        # Verify token
        email = security_manager.verify_password_reset_token(reset_data.token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Find user
        user = await User.find_one(User.email == email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check token expiry
        if (user.password_reset_expires and 
            user.password_reset_expires < datetime.utcnow()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )
        
        # Update password
        user.password_hash = security_manager.hash_password(reset_data.new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        user.updated_at = datetime.utcnow()
        await user.save()
        
        # Invalidate all sessions
        await sessions.delete_user_sessions(str(user.id))
        
        # Log action
        background_tasks.add_task(
            log_user_action,
            str(user.id),
            "password_reset_completed",
            {"email": email}
        )
        
        logger.info(f"Password reset completed: {email}")
        
        return {
            "success": True,
            "message": "Password reset successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset confirmation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )