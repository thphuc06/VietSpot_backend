"""
API Dependencies
Các dependency functions dùng chung cho các endpoints
"""

from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
import jwt
from jwt.algorithms import ECAlgorithm, RSAAlgorithm
from jwt.exceptions import InvalidTokenError
import requests
import json

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

# Cache for JWKS keys (in production, use Redis or similar)
_jwks_cache = None


def get_jwks_keys():
    """
    Fetch JWKS keys from Supabase.
    Uses simple in-memory caching.
    """
    global _jwks_cache
    if _jwks_cache is None:
        try:
            response = requests.get(JWKS_URL, timeout=5)
            response.raise_for_status()
            _jwks_cache = response.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to fetch JWKS keys from {JWKS_URL}: {str(e)}"
            )
    return _jwks_cache


def verify_jwt_token(token: str) -> dict:
    """
    Verify Supabase JWT token using ES256/RS256 and JWKS public keys.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload containing user info
        
    Raises:
        HTTPException 401 if token is invalid
    """
    try:
        # Get the token header to find the Key ID (kid)
        header = jwt.get_unverified_header(token)
        kid = header.get('kid')
        alg = header.get('alg')
        
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing 'kid' in header",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Fetch JWKS keys
        jwks = get_jwks_keys()
        
        # Find the matching public key
        public_key = None
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                # Convert JWK to public key based on algorithm
                if alg == 'ES256':
                    public_key = ECAlgorithm.from_jwk(json.dumps(key))
                elif alg == 'RS256':
                    public_key = RSAAlgorithm.from_jwk(json.dumps(key))
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Unsupported algorithm: {alg}",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                break
        
        if not public_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Public key with kid '{kid}' not found in JWKS endpoint. "
                       f"Token may be from a different Supabase project.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Decode and verify JWT token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[alg],  # Use the algorithm from token header
            audience="authenticated"
        )
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
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
