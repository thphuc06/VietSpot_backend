"""
User Schemas
Schemas cho user
"""

from pydantic import BaseModel
from typing import Optional, List, Any


class UserCommentedPlace(BaseModel):
    """Schema cho place mà user đã comment"""
    id: str
    name: Optional[str] = None
    address: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[float] = None
    coordinates: Optional[Any] = None


class UserCommentedPlacesResponse(BaseModel):
    """Response schema cho danh sách places đã comment"""
    success: bool
    count: int
    places: List[UserCommentedPlace]
