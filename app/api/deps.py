"""
API Dependencies
Các dependency functions dùng chung cho các endpoints
"""

from typing import Optional
from fastapi import Header, HTTPException
from supabase import Client

from app.services.supabase_client import get_supabase_client


def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> str:
    """
    Lấy user_id từ header.
    Trong thực tế sẽ dùng JWT token để xác thực.
    
    Args:
        x_user_id: Header X-User-ID
        
    Returns:
        user_id string
        
    Raises:
        HTTPException 401 nếu thiếu header
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-ID header")
    return x_user_id


def get_optional_user_id(x_user_id: Optional[str] = Header(None)) -> Optional[str]:
    """
    Lấy user_id từ header (optional).
    Dùng cho các endpoint không bắt buộc đăng nhập.
    """
    return x_user_id


def get_db() -> Client:
    """
    Get Supabase client dependency.
    """
    return get_supabase_client()
