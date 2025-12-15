"""
Storage Service
Xử lý upload/delete files lên Supabase Storage
"""

import uuid
import time
import mimetypes
from typing import List
from fastapi import UploadFile, HTTPException

from app.core.config import settings
from app.services.supabase_client import get_supabase_client


async def upload_images(
    files: List[UploadFile],
    user_id: str,
    max_files: int = 5
) -> List[str]:
    """
    Upload nhiều ảnh lên Supabase Storage.
    
    Args:
        files: Danh sách file ảnh
        user_id: ID của user upload
        max_files: Số file tối đa cho phép
        
    Returns:
        Danh sách URLs của ảnh đã upload
    """
    if len(files) > max_files:
        raise HTTPException(
            status_code=400, 
            detail=f"Tối đa {max_files} ảnh mỗi lần upload"
        )
    
    supabase = get_supabase_client()
    image_urls = []
    
    for file in files:
        # Kiểm tra loại file
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail=f"File {file.filename} không phải ảnh"
            )
        
        # Tạo tên file unique
        file_ext = mimetypes.guess_extension(file.content_type) or ".jpg"
        file_name = f"reviews/{user_id}/{int(time.time())}_{uuid.uuid4()}{file_ext}"
        
        try:
            # Đọc file content
            content = await file.read()
            
            # Upload lên Supabase Storage
            supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
                path=file_name,
                file=content,
                file_options={"content-type": file.content_type}
            )
            
            # Lấy Public URL
            public_url = supabase.storage.from_(settings.SUPABASE_BUCKET).get_public_url(file_name)
            
            if isinstance(public_url, str):
                image_urls.append(public_url)
            else:
                image_urls.append(str(public_url))
                
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Lỗi upload ảnh {file.filename}: {str(e)}"
            )
    
    return image_urls


async def delete_image(file_path: str) -> bool:
    """
    Xóa ảnh khỏi Supabase Storage.
    
    Args:
        file_path: Đường dẫn file trong bucket
        
    Returns:
        True nếu xóa thành công
    """
    try:
        supabase = get_supabase_client()
        supabase.storage.from_(settings.SUPABASE_BUCKET).remove([file_path])
        return True
    except Exception:
        return False
