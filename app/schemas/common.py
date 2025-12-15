"""
Common Schemas
Các schema dùng chung cho nhiều endpoints
"""

from pydantic import BaseModel
from typing import Optional, Any


class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool
    message: str
    data: Optional[Any] = None


class PaginationParams(BaseModel):
    """Pagination parameters"""
    limit: int = 20
    offset: int = 0
