"""
Image Schemas
Schemas cho hình ảnh
"""

from pydantic import BaseModel, field_serializer
from typing import Optional, List
from datetime import datetime

from app.core.datetime_utils import format_iso8601_vietnam


class ImageResponse(BaseModel):
    """Response schema cho một image"""
    id: str
    url: str
    place_id: Optional[str] = None
    comment_id: Optional[str] = None
    is_scraped: Optional[bool] = None
    uploaded_at: Optional[datetime] = None

    @field_serializer('uploaded_at')
    def serialize_uploaded_at(self, dt: Optional[datetime], _info) -> Optional[str]:
        """
        Serialize uploaded_at to ISO 8601 string in Vietnam timezone.
        Converts from UTC (storage) to UTC+7 (API response).
        """
        if dt is None:
            return None
        return format_iso8601_vietnam(dt)


class ImageUploadResponse(BaseModel):
    """Response sau khi upload images"""
    success: bool
    message: str
    urls: List[str]
