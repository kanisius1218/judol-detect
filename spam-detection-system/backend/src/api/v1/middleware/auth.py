"""
Authentication middleware for API security.
Implements JWT, API key, and OAuth authentication.
"""
from typing import Optional, Tuple, List
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from ....core import (
    settings,
    SecurityUtils,
    TokenData,
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError,
    APIKeyInvalidError,
    logger
)
from ....repository.user_repository import UserRepository
from ....repository.api_key_repository import APIKeyRepository
from ....models.database.user import User
from ....api.deps import get_db


# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


class AuthMiddleware:
    """Authentication middleware for request validation."""
    
    def __init__(self):
        self.security = SecurityUtils()
        self.user_repo = UserRepository()
        self.api_key_repo = APIKeyRepository()
    
    async def get_current_user_from_token(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """Get current user from JWT token."""
        if not credentials:
            raise AuthenticationError("Missing authentication credentials")
        
        try:
            # Decode token
            token_data = self.security.decode_token(credentials.credentials)
            
            if not token_data:
                raise InvalidTokenError()
            
            # Check token type
            if token_data.token_type != "access":
                raise InvalidTokenError("Invalid token type")
            
            # Get user from database
            user = await self.user_repo.get_by_id(db, user_id=token_data.sub)
            
            if not user:
                raise InvalidTokenError("User not found")
            
            if not user.is_active:
                raise AuthenticationError("User account is inactive")
            
            # Add scopes to user object
            user.scopes = token_data.scopes
            
            return user
            
        except JWTError as e:
            logger.error(f"JWT decode error: {str(e)}")
            raise InvalidTokenError("Could not validate token")
    
    async def get_current_user_from_api_key(
        self,
        api_key: str = Depends(api_key_header),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """Get current user from API key."""
        if not api_key:
            raise APIKeyInvalidError("Missing API key")
        
        # Look up API key
        key_record = await self.api_key_repo.get_by_key(db, api_key)
        
        if not key_record:
            raise APIKeyInvalidError()
        
        if not key_record.is_active:
            raise APIKeyInvalidError("API key is inactive")
        
        # Check rate limits
        if not await self.api_key_repo.check_rate_limit(db, key_record.id):
            from ....core.exceptions import RateLimitExceededError
            raise RateLimitExceededError(retry_after=60)
        
        # Update last used timestamp
        await self.api_key_repo.update_last_used(db, key_record.id)
        
        # Get associated user
        user = await self.user_repo.get_by_id(db, user_id=key_record.user_id)
        
        if not user:
            raise APIKeyInvalidError("Associated user not found")
        
        if not user.is_active:
            raise APIKeyInvalidError("User account is inactive")
        
        # Add API key scopes to user
        user.scopes = key_record.scopes
        user.api_key_id = key_record.id
        
        return user
    
    async def get_current_user(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
        api_key: Optional[str] = Depends(api_key_header),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """
        Get current user from either JWT token or API key.
        Prefers JWT token if both are provided.
        """
        if credentials:
            return await self.get_current_user_from_token(credentials, db)
        elif api_key:
            return await self.get_current_user_from_api_key(api_key, db)
        else:
            raise AuthenticationError("No authentication credentials provided")
    
    async def get_optional_user(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
        api_key: Optional[str] = Depends(api_key_header),
        db: AsyncSession = Depends(get_db)
    ) -> Optional[User]:
        """Get current user if authenticated, otherwise None."""
        try:
            return await self.get_current_user(credentials, api_key, db)
        except (AuthenticationError, InvalidTokenError, APIKeyInvalidError):
            return None
    
    def require_scopes(self, required_scopes: List[str]):
        """
        Dependency to require specific scopes.
        
        Usage:
            @router.get("/admin", dependencies=[Depends(auth.require_scopes(["admin"]))])
        """
        async def scope_checker(
            current_user: User = Depends(self.get_current_user)
        ) -> User:
            """Check if user has required scopes."""
            user_scopes = getattr(current_user, 'scopes', [])
            
            for scope in required_scopes:
                if scope not in user_scopes and "admin" not in user_scopes:
                    from ....core.exceptions import InsufficientPermissionsError
                    raise InsufficientPermissionsError(
                        required_permission=scope,
                        message=f"Scope '{scope}' is required"
                    )
            
            return current_user
        
        return scope_checker
    
    def require_permission(self, permission: str):
        """
        Dependency to require specific permission.
        
        Usage:
            @router.delete("/spam", dependencies=[Depends(auth.require_permission(Permission.DELETE))])
        """
        async def permission_checker(
            current_user: User = Depends(self.get_current_user)
        ) -> User:
            """Check if user has required permission."""
            from ....core import check_permission
            
            if not check_permission(current_user.role, permission):
                from ....core.exceptions import InsufficientPermissionsError
                raise InsufficientPermissionsError(
                    required_permission=permission,
                    message=f"Permission '{permission}' is required for role '{current_user.role}'"
                )
            
            return current_user
        
        return permission_checker
    
    async def get_admin_user(
        self,
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Require admin user."""
        if current_user.role != "admin":
            from ....core.exceptions import InsufficientPermissionsError
            raise InsufficientPermissionsError(
                required_permission="admin",
                message="Admin access required"
            )
        
        return current_user


# OAuth providers support
class OAuthProvider:
    """OAuth authentication provider base class."""
    
    def __init__(self, provider_name: str):
        self.provider = provider_name
    
    async def authenticate(self, token: str) -> Optional[dict]:
        """Authenticate with OAuth provider."""
        raise NotImplementedError
    
    async def get_user_info(self, token: str) -> dict:
        """Get user information from OAuth provider."""
        raise NotImplementedError


class GoogleOAuth(OAuthProvider):
    """Google OAuth authentication."""
    
    def __init__(self):
        super().__init__("google")
        self.client_id = settings.YOUTUBE_CLIENT_ID
        self.client_secret = settings.YOUTUBE_CLIENT_SECRET
    
    async def authenticate(self, token: str) -> Optional[dict]:
        """Verify Google OAuth token."""
        from google.oauth2 import id_token
        from google.auth.transport import requests
        
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                self.client_id
            )
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                return None
            
            return idinfo
            
        except ValueError:
            return None
    
    async def get_user_info(self, token: str) -> dict:
        """Get user info from Google."""
        idinfo = await self.authenticate(token)
        
        if not idinfo:
            return {}
        
        return {
            'id': idinfo['sub'],
            'email': idinfo.get('email'),
            'name': idinfo.get('name'),
            'picture': idinfo.get('picture'),
            'email_verified': idinfo.get('email_verified', False)
        }


# Singleton instances
auth = AuthMiddleware()
google_oauth = GoogleOAuth()


# Dependency shortcuts
get_current_user = auth.get_current_user
get_optional_user = auth.get_optional_user
get_admin_user = auth.get_admin_user
require_scopes = auth.require_scopes
require_permission = auth.require_permission
