"""Place Schemas - Match với database schema thực tế"""

from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional, List, Any
from datetime import datetime

from app.core.datetime_utils import format_iso8601_vietnam


class Coordinates(BaseModel):
    """Schema cho coordinates (jsonb)"""
    lat: Optional[float] = None
    lon: Optional[float] = None


class PlaceBase(BaseModel):
    """Base Place schema - theo đúng database"""
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    opening_hours: Optional[dict] = None  # jsonb
    about: Optional[dict] = None  # jsonb
    coordinates: Optional[dict] = None  # jsonb {lat, lon}


class PlaceCreate(PlaceBase):
    """Schema for creating a new Place."""
    pass


class PlaceUpdate(BaseModel):
    """Schema for updating a Place."""
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    opening_hours: Optional[dict] = None
    about: Optional[dict] = None
    coordinates: Optional[dict] = None


class Place(PlaceBase):
    """Schema for Place in API responses."""
    id: str
    original_url: Optional[str] = None
    created_at: Optional[datetime] = None
    is_scraped: Optional[bool] = None
    images: Optional[List[dict]] = []
    comments: Optional[List[dict]] = []
    comments_count: Optional[int] = 0

    @field_serializer('created_at')
    def serialize_created_at(self, dt: Optional[datetime], _info) -> Optional[str]:
        """
        Serialize created_at to ISO 8601 string in Vietnam timezone.
        Converts from UTC (storage) to UTC+7 (API response).
        """
        if dt is None:
            return None
        return format_iso8601_vietnam(dt)

    model_config = ConfigDict(from_attributes=True)


class PlaceListResponse(Place):
    """
    Schema cho danh sách places với thông tin khoảng cách.
    Dùng khi có lat/lon filter.
    """
    distance_km: Optional[float] = None  # Khoảng cách tính bằng km
    distance_m: Optional[float] = None   # Khoảng cách tính bằng meters (từ RPC)


class PlaceSearchResponse(PlaceBase):
    """
    Schema cho kết quả tìm kiếm địa điểm (search_places function).
    Bao gồm match_score và distance_km.
    """
    id: str
    distance_km: Optional[float] = None  # Khoảng cách từ user (nếu có lat/lon)
    distance_m: Optional[int] = None     # Khoảng cách tính bằng meters
    match_score: Optional[float] = None  # Điểm số giống nhau (similarity score)
    images: Optional[List[dict]] = []

    model_config = ConfigDict(from_attributes=True)
