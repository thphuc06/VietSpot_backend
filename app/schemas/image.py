"""
Image Schemas
Schemas cho hình ảnh
"""

from pydantic import BaseModel
from typing import Optional, List


class ImageResponse(BaseModel):
    """Response schema cho một image"""
    id: str
    url: str
    place_id: Optional[str] = None
    comment_id: Optional[str] = None
    is_scraped: Optional[bool] = None
    uploaded_at: Optional[str] = None


class ImageUploadResponse(BaseModel):
    """Response sau khi upload images"""
    success: bool
    message: str
    urls: List[str]
