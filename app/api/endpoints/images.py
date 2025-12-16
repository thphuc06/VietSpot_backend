"""
Images Endpoints
Xử lý các API liên quan đến hình ảnh
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
from supabase import Client

from app.api.deps import get_current_user_id, get_db
from app.schemas.image import ImageResponse, ImageUploadResponse
from app.services import storage

router = APIRouter()


@router.get("/places/{place_id}/images", response_model=List[ImageResponse])
async def get_place_images(
    place_id: str,
    db: Client = Depends(get_db)
):
    """
    Lấy danh sách hình ảnh của một địa điểm.
    
    - **place_id**: UUID của địa điểm
    """
    try:
        response = db.table('images').select('*').eq('place_id', place_id).execute()
        
        if hasattr(response, 'data'):
            return response.data
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy ảnh: {str(e)}")


@router.get("/comments/{comment_id}/images", response_model=List[ImageResponse])
async def get_comment_images(
    comment_id: str,
    db: Client = Depends(get_db)
):
    """
    Lấy danh sách hình ảnh của một comment.
    
    - **comment_id**: UUID của comment
    """
    try:
        response = db.table('images').select('*').eq('comment_id', comment_id).execute()
        
        if hasattr(response, 'data'):
            return response.data
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy ảnh comment: {str(e)}")


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_images(
    files: List[UploadFile] = File(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Upload nhiều ảnh lên Supabase Storage.
    Requires JWT authentication.
    
    - **files**: Danh sách file ảnh (tối đa 5 file)
    
    Returns: Danh sách URLs của ảnh đã upload
    """
    image_urls = await storage.upload_images(files, user_id, max_files=5)
    
    return ImageUploadResponse(
        success=True,
        message=f"Đã upload {len(image_urls)} ảnh",
        urls=image_urls
    )
