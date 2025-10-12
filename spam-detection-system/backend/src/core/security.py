"""
Security utilities for authentication, authorization, and encryption.
Implements JWT, API key validation, and password hashing.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel
import secrets
import hashlib
import hmac
from functools import wraps
import re
from .config import settings


# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS
)


class TokenData(BaseModel):
    """JWT Token payload schema."""
    sub: str  # Subject (user_id)
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
    scopes: list[str] = []
    token_type: str = "access"


class SecurityUtils:
    """Core security utilities."""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, list[str]]:
        """
        Validate password strength.
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
        
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Password must contain at least one special character")
        
        # Check for common passwords (in production, use a proper list)
        common_passwords = ["password", "12345678", "qwerty", "admin"]
        if password.lower() in common_passwords:
            errors.append("Password is too common")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def create_access_token(
        subject: str,
        scopes: list[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.utcnow(),
            "scopes": scopes or [],
            "token_type": "access"
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(subject: str) -> str:
        """Create a JWT refresh token."""
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        to_encode = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.utcnow(),
            "token_type": "refresh"
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[TokenData]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY.get_secret_value(),
                algorithms=[settings.JWT_ALGORITHM]
            )
            return TokenData(**payload)
        except JWTError:
            return None
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def verify_api_key(api_key: str, hashed_key: str) -> bool:
        """Verify an API key against its hash."""
        return SecurityUtils.hash_api_key(api_key) == hashed_key
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate a CSRF token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def verify_csrf_token(token: str, expected: str) -> bool:
        """Verify a CSRF token using constant-time comparison."""
        return hmac.compare_digest(token, expected)
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 10000) -> str:
        """
        Sanitize user input to prevent injection attacks.
        """
        if not text:
            return ""
        
        # Truncate to max length
        text = text[:max_length]
        
        # Remove null bytes
        text = text.replace("\x00", "")
        
        # Remove control characters except newlines and tabs
        import unicodedata
        allowed_chars = ["\n", "\t", "\r"]
        text = "".join(
            char for char in text
            if char in allowed_chars or not unicodedata.category(char).startswith("C")
        )
        
        return text.strip()
    
    @staticmethod
    def mask_sensitive_data(data: str, mask_percentage: float = 0.75) -> str:
        """
        Mask sensitive data for logging.
        Shows only the first few characters.
        """
        if not data or len(data) < 4:
            return "****"
        
        visible_chars = max(1, int(len(data) * (1 - mask_percentage)))
        visible_chars = min(visible_chars, 4)  # Show max 4 chars
        
        return data[:visible_chars] + "*" * (len(data) - visible_chars)
    
    @staticmethod
    def is_safe_redirect_url(url: str, allowed_hosts: list[str]) -> bool:
        """
        Check if a redirect URL is safe.
        Prevents open redirect vulnerabilities.
        """
        from urllib.parse import urlparse
        
        if not url:
            return False
        
        # Parse the URL
        parsed = urlparse(url)
        
        # Check if it's a relative URL (safe)
        if not parsed.netloc:
            return True
        
        # Check if the host is in the allowed list
        return parsed.netloc in allowed_hosts
    
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate a one-time password."""
        return "".join(secrets.choice("0123456789") for _ in range(length))
    
    @staticmethod
    def encrypt_data(data: str, key: Optional[str] = None) -> str:
        """
        Encrypt sensitive data using Fernet (symmetric encryption).
        In production, use proper key management (e.g., AWS KMS, HashiCorp Vault).
        """
        from cryptography.fernet import Fernet
        
        if not key:
            key = settings.SECRET_KEY.get_secret_value()
        
        # Derive a proper Fernet key from the secret
        import base64
        key_bytes = hashlib.sha256(key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        
        f = Fernet(fernet_key)
        encrypted = f.encrypt(data.encode())
        
        return base64.urlsafe_b64encode(encrypted).decode()
    
    @staticmethod
    def decrypt_data(encrypted_data: str, key: Optional[str] = None) -> str:
        """
        Decrypt data encrypted with encrypt_data.
        """
        from cryptography.fernet import Fernet
        import base64
        
        if not key:
            key = settings.SECRET_KEY.get_secret_value()
        
        # Derive the same Fernet key
        key_bytes = hashlib.sha256(key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        
        f = Fernet(fernet_key)
        decrypted = f.decrypt(base64.urlsafe_b64decode(encrypted_data))
        
        return decrypted.decode()


class RateLimiter:
    """Rate limiting implementation using token bucket algorithm."""
    
    def __init__(self, rate: int = 60, per: int = 60, burst: int = 10):
        """
        Initialize rate limiter.
        
        Args:
            rate: Number of requests allowed
            per: Time period in seconds
            burst: Maximum burst size
        """
        self.rate = rate
        self.per = per
        self.burst = burst
        self.allowance = rate
        self.last_check = datetime.utcnow()
    
    def is_allowed(self) -> bool:
        """Check if request is allowed."""
        current = datetime.utcnow()
        time_passed = (current - self.last_check).total_seconds()
        
        self.last_check = current
        self.allowance += time_passed * (self.rate / self.per)
        
        if self.allowance > self.rate + self.burst:
            self.allowance = self.rate + self.burst
        
        if self.allowance < 1.0:
            return False
        
        self.allowance -= 1.0
        return True


# Permission system
class Permission:
    """Permission constants."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    MODERATE = "moderate"
    ANALYZE = "analyze"
    EXPORT = "export"
    AUTO_DELETE = "auto_delete"
    MANUAL_DELETE = "manual_delete"
    ROLLBACK = "rollback"


class Role:
    """Role definitions with permissions."""
    
    USER = {
        "name": "user",
        "permissions": [Permission.READ]
    }
    
    MODERATOR = {
        "name": "moderator",
        "permissions": [
            Permission.READ,
            Permission.WRITE,
            Permission.MODERATE,
            Permission.MANUAL_DELETE
        ]
    }
    
    ANALYST = {
        "name": "analyst",
        "permissions": [
            Permission.READ,
            Permission.ANALYZE,
            Permission.EXPORT
        ]
    }
    
    ADMIN = {
        "name": "admin",
        "permissions": [
            Permission.READ,
            Permission.WRITE,
            Permission.DELETE,
            Permission.ADMIN,
            Permission.MODERATE,
            Permission.ANALYZE,
            Permission.EXPORT,
            Permission.AUTO_DELETE,
            Permission.MANUAL_DELETE,
            Permission.ROLLBACK
        ]
    }


def check_permission(user_role: str, required_permission: str) -> bool:
    """Check if a role has the required permission."""
    role_map = {
        "user": Role.USER,
        "moderator": Role.MODERATOR,
        "analyst": Role.ANALYST,
        "admin": Role.ADMIN
    }
    
    role = role_map.get(user_role.lower())
    if not role:
        return False
    
    return required_permission in role["permissions"]
