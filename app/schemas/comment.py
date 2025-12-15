"""
Comment Schemas
Schemas cho comments/reviews
"""

from pydantic import BaseModel, Field
from typing import Optional, List

from app.schemas.image import ImageResponse


class CommentResponse(BaseModel):
    """Response schema cho một comment"""
    id: str
    place_id: str
    user_id: Optional[str] = None
    author: Optional[str] = None
    rating: Optional[float] = None
    text: Optional[str] = None
    date: Optional[str] = None
    images: List[ImageResponse] = []


class CreateCommentRequest(BaseModel):
    """Request schema để tạo comment mới"""
    place_id: str
    user_id: Optional[str] = None  # Optional - có thể để trống cho khách
    author_name: str = "Khách tham quan"
    rating: int = Field(ge=0, le=5, default=5)
    text: Optional[str] = None
    image_urls: List[str] = []  # URLs sau khi đã upload


class UpdateCommentRequest(BaseModel):
    """Request schema để cập nhật comment"""
    author_name: Optional[str] = None
    rating: Optional[int] = Field(ge=0, le=5, default=None)
    text: Optional[str] = None


class AddImagesToCommentRequest(BaseModel):
    """Request schema để thêm ảnh vào comment"""
    image_urls: List[str]
