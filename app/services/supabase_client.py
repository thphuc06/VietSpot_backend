"""
Supabase Client Service
Singleton pattern để quản lý connection đến Supabase
"""

from supabase import create_client, Client
from functools import lru_cache

from app.core.config import settings


@lru_cache()
def get_supabase_client() -> Client:
    """
    Tạo và trả về Supabase client (singleton).
    Sử dụng lru_cache để đảm bảo chỉ tạo 1 instance.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


# Shortcut để dùng trong code
supabase = get_supabase_client()
