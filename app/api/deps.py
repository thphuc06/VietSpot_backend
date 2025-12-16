"""
API Dependencies
Các dependency functions dùng chung cho các endpoints
"""

from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError

from app.services.supabase_client import get_supabase_client
from app.core.config import settings

# Security scheme for JWT Bearer token
# auto_error=True will automatically return 401 if token is missing
security = HTTPBearer(
    scheme_name="Bearer",
    description="Enter your Supabase JWT token",
    auto_error=True
)

# JWKS URL for fetching Supabase public keys
JWKS_URL = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"

# Create PyJWKClient to automatically fetch and cache public keys
jwks_client = PyJWKClient(JWKS_URL)


def verify_jwt_token(token: str) -> dict:
    """
    Verify Supabase JWT token using RS256 and JWKS public keys.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload containing user info
        
    Raises:
        HTTPException 401 if token is invalid
    """
    try:
        # Get the signing key from the JWKS endpoint
        # This automatically fetches the public key based on the token's key ID (kid)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Decode and verify JWT token using RS256 algorithm
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="authenticated"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Get current authenticated user from JWT token.
    Required for protected endpoints.
    
    Args:
        credentials: HTTP Bearer credentials containing JWT token
        
    Returns:
        User payload from verified JWT token
        
    Raises:
        HTTPException 401 if authentication fails
    """
    token = credentials.credentials
    payload = verify_jwt_token(token)
    return payload


def get_current_user_id(user: dict = Depends(get_current_user)) -> str:
    """
    Extract user_id from authenticated user payload.
    
    Args:
        user: Authenticated user payload
        
    Returns:
        User ID string
        
    Raises:
        HTTPException 401 if user_id not found in token
    """
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token"
        )
    return user_id


def get_optional_current_user(
    authorization: Optional[str] = Header(None)
) -> Optional[dict]:
    """
    Get current user if authenticated, otherwise return None.
    Used for endpoints that work with or without authentication.
    
    Args:
        authorization: Authorization header (optional)
        
    Returns:
        User payload if authenticated, None otherwise
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = verify_jwt_token(token)
        return payload
    except HTTPException:
        return None


def get_optional_user_id(user: Optional[dict] = Depends(get_optional_current_user)) -> Optional[str]:
    """
    Extract user_id from optional authenticated user.
    
    Args:
        user: Optional user payload
        
    Returns:
        User ID if authenticated, None otherwise
    """
    if user:
        return user.get("sub")
    return None


def get_db() -> Client:
    """
    Get Supabase client dependency.
    """
    return get_supabase_client()
