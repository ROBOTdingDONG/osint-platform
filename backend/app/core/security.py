"""
Security utilities for authentication and authorization
JWT token handling, password hashing, and permission management
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import pyotp
import qrcode
from io import BytesIO
import base64

from app.core.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


class SecurityManager:
    """
    Centralized security management for the application
    Handles password hashing, JWT tokens, and MFA
    """
    
    def __init__(self):
        self.pwd_context = pwd_context
        self.algorithm = settings.ALGORITHM
        self.secret_key = settings.SECRET_KEY
    
    # Password Management
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            plain_password: Plain text password
            hashed_password: Stored hash
            
        Returns:
            True if password matches
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Validate password strength and return detailed feedback
        
        Args:
            password: Password to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            "valid": True,
            "score": 0,
            "feedback": [],
            "requirements": {
                "min_length": False,
                "has_upper": False,
                "has_lower": False,
                "has_digit": False,
                "has_special": False
            }
        }
        
        # Check minimum length
        if len(password) >= settings.PASSWORD_MIN_LENGTH:
            result["requirements"]["min_length"] = True
            result["score"] += 20
        else:
            result["valid"] = False
            result["feedback"].append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
        
        # Check for uppercase letters
        if any(c.isupper() for c in password):
            result["requirements"]["has_upper"] = True
            result["score"] += 20
        else:
            result["feedback"].append("Password must contain at least one uppercase letter")
        
        # Check for lowercase letters
        if any(c.islower() for c in password):
            result["requirements"]["has_lower"] = True
            result["score"] += 20
        else:
            result["feedback"].append("Password must contain at least one lowercase letter")
        
        # Check for digits
        if any(c.isdigit() for c in password):
            result["requirements"]["has_digit"] = True
            result["score"] += 20
        else:
            result["feedback"].append("Password must contain at least one digit")
        
        # Check for special characters
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if any(c in special_chars for c in password):
            result["requirements"]["has_special"] = True
            result["score"] += 20
        else:
            result["feedback"].append("Password must contain at least one special character")
        
        # Additional strength checks
        if len(password) >= 12:
            result["score"] += 10
        
        if not any(password[i:i+3] in password[i+3:] for i in range(len(password)-2)):
            result["score"] += 10
        
        # Final validation
        if not all(result["requirements"].values()):
            result["valid"] = False
        
        return result
    
    # JWT Token Management
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token
        
        Args:
            data: Data to encode in token
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT refresh token
        
        Args:
            data: Data to encode in token
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT refresh token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def create_email_verification_token(self, email: str) -> str:
        """
        Create a token for email verification
        
        Args:
            email: Email address to verify
            
        Returns:
            Verification token
        """
        data = {
            "email": email,
            "type": "email_verification"
        }
        expire = datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
        data.update({"exp": expire})
        
        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)
    
    def verify_email_verification_token(self, token: str) -> Optional[str]:
        """
        Verify email verification token and return email
        
        Args:
            token: Verification token
            
        Returns:
            Email address if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") == "email_verification":
                return payload.get("email")
        except JWTError:
            pass
        return None
    
    def create_password_reset_token(self, email: str) -> str:
        """
        Create a token for password reset
        
        Args:
            email: Email address for password reset
            
        Returns:
            Password reset token
        """
        data = {
            "email": email,
            "type": "password_reset"
        }
        expire = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        data.update({"exp": expire})
        
        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)
    
    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """
        Verify password reset token and return email
        
        Args:
            token: Password reset token
            
        Returns:
            Email address if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") == "password_reset":
                return payload.get("email")
        except JWTError:
            pass
        return None
    
    # Multi-Factor Authentication
    def generate_mfa_secret(self) -> str:
        """
        Generate a new MFA secret for TOTP
        
        Returns:
            Base32 encoded secret
        """
        return pyotp.random_base32()
    
    def generate_qr_code(self, email: str, secret: str) -> str:
        """
        Generate QR code for MFA setup
        
        Args:
            email: User's email address
            secret: MFA secret
            
        Returns:
            Base64 encoded QR code image
        """
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name="OSINT Platform"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def verify_mfa_token(self, secret: str, token: str) -> bool:
        """
        Verify MFA TOTP token
        
        Args:
            secret: User's MFA secret
            token: TOTP token to verify
            
        Returns:
            True if token is valid
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    # API Key Management
    def generate_api_key(self) -> str:
        """
        Generate a secure API key
        
        Returns:
            API key string
        """
        return f"osint_{secrets.token_urlsafe(32)}"
    
    def hash_api_key(self, api_key: str) -> str:
        """
        Hash an API key for storage
        
        Args:
            api_key: Plain API key
            
        Returns:
            Hashed API key
        """
        return self.hash_password(api_key)
    
    def verify_api_key(self, plain_key: str, hashed_key: str) -> bool:
        """
        Verify an API key against its hash
        
        Args:
            plain_key: Plain API key
            hashed_key: Stored hash
            
        Returns:
            True if API key matches
        """
        return self.verify_password(plain_key, hashed_key)


# Global security manager instance
security_manager = SecurityManager()


# Permission constants
class Permissions:
    """
    Define all available permissions in the system
    """
    # Data permissions
    READ_DATA = "read:data"
    WRITE_DATA = "write:data"
    DELETE_DATA = "delete:data"
    
    # Collection permissions
    READ_COLLECTORS = "read:collectors"
    WRITE_COLLECTORS = "write:collectors"
    EXECUTE_COLLECTORS = "execute:collectors"
    
    # Report permissions
    READ_REPORTS = "read:reports"
    WRITE_REPORTS = "write:reports"
    SHARE_REPORTS = "share:reports"
    
    # User permissions
    READ_USERS = "read:users"
    WRITE_USERS = "write:users"
    ADMIN_USERS = "admin:users"
    
    # Organization permissions
    READ_ORGANIZATION = "read:organization"
    WRITE_ORGANIZATION = "write:organization"
    ADMIN_ORGANIZATION = "admin:organization"
    
    # System permissions
    READ_SYSTEM = "read:system"
    WRITE_SYSTEM = "write:system"
    ADMIN_SYSTEM = "admin:system"


# Role definitions
ROLE_PERMISSIONS = {
    "admin": [
        Permissions.READ_DATA, Permissions.WRITE_DATA, Permissions.DELETE_DATA,
        Permissions.READ_COLLECTORS, Permissions.WRITE_COLLECTORS, Permissions.EXECUTE_COLLECTORS,
        Permissions.READ_REPORTS, Permissions.WRITE_REPORTS, Permissions.SHARE_REPORTS,
        Permissions.READ_USERS, Permissions.WRITE_USERS, Permissions.ADMIN_USERS,
        Permissions.READ_ORGANIZATION, Permissions.WRITE_ORGANIZATION, Permissions.ADMIN_ORGANIZATION,
        Permissions.READ_SYSTEM, Permissions.WRITE_SYSTEM, Permissions.ADMIN_SYSTEM,
    ],
    "manager": [
        Permissions.READ_DATA, Permissions.WRITE_DATA,
        Permissions.READ_COLLECTORS, Permissions.WRITE_COLLECTORS, Permissions.EXECUTE_COLLECTORS,
        Permissions.READ_REPORTS, Permissions.WRITE_REPORTS, Permissions.SHARE_REPORTS,
        Permissions.READ_USERS, Permissions.WRITE_USERS,
        Permissions.READ_ORGANIZATION,
    ],
    "analyst": [
        Permissions.READ_DATA,
        Permissions.READ_COLLECTORS, Permissions.EXECUTE_COLLECTORS,
        Permissions.READ_REPORTS, Permissions.WRITE_REPORTS,
    ],
    "viewer": [
        Permissions.READ_DATA,
        Permissions.READ_COLLECTORS,
        Permissions.READ_REPORTS,
    ],
    "api_user": []
}


def get_permissions_for_role(role: str) -> List[str]:
    """
    Get permissions for a given role
    
    Args:
        role: Role name
        
    Returns:
        List of permissions
    """
    return ROLE_PERMISSIONS.get(role, [])


def check_permission(user_permissions: List[str], required_permission: str) -> bool:
    """
    Check if user has required permission
    
    Args:
        user_permissions: List of user's permissions
        required_permission: Required permission
        
    Returns:
        True if user has permission
    """
    return required_permission in user_permissions