"""
Comments Endpoints
Xử lý các API liên quan đến comments/reviews
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from supabase import Client
from datetime import datetime
import uuid

from app.api.deps import get_current_user_id, get_db
from app.core.datetime_utils import get_utc_now
from app.schemas.comment import (
    CommentResponse,
    CreateCommentRequest,
    UpdateCommentRequest,
    AddImagesToCommentRequest
)
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("/places/{place_id}/comments", response_model=List[CommentResponse])
async def get_place_comments(
    place_id: str,
    limit: int = 20,
    offset: int = 0,
    order_by: str = "recent",  # recent, rating_desc, rating_asc
    db: Client = Depends(get_db)
):
    """Lấy danh sách comments của một địa điểm. Sử dụng RPC get_comments_by_place."""
    try:
        response = db.rpc("get_comments_by_place", {
            "p_place_id": place_id,
            "p_limit": limit,
            "p_offset": offset,
            "p_order_by": order_by
        }).execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy comments: {str(e)}")


@router.post("/comments", response_model=APIResponse)
async def create_comment(
    request: CreateCommentRequest,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Tạo comment mới cho một địa điểm.
    Requires JWT authentication.
    """
    try:
        # Use authenticated user_id from JWT token
        
        # Gọi RPC function - xử lý tất cả: validate place, tạo user, insert comment + images
        response = db.rpc("create_user_content", {
            "p_place_id": request.place_id,
            "p_user_id": user_id,
            "p_author_name": request.author_name or "Khách tham quan",
            "p_rating": request.rating,
            "p_text": request.text,
            "p_image_urls": request.image_urls if request.image_urls else []
        }).execute()
        
        if response.data:
            result = response.data[0] if isinstance(response.data, list) else response.data
            
            if result.get("success"):
                return APIResponse(
                    success=True,
                    message=result.get("message", "Đã tạo comment thành công"),
                    data={
                        "comment_id": str(result.get("comment_id")),
                        "user_id": user_id,
                        "images_count": result.get("images_count", 0)
                    }
                )
            else:
                raise HTTPException(status_code=400, detail=result.get("message", "Lỗi tạo comment"))
        
        raise HTTPException(status_code=500, detail="Không nhận được response từ database")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo comment: {str(e)}")


@router.put("/comments/{comment_id}", response_model=APIResponse)
async def update_comment(
    comment_id: str,
    request: UpdateCommentRequest,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_db)
):
    """
    Chỉnh sửa comment (chỉ owner mới được sửa).
    Requires JWT authentication.
    
    - **comment_id**: UUID của comment cần sửa
    """
    try:
        # Kiểm tra comment tồn tại và quyền sở hữu
        check_response = db.table('comments').select('user_id').eq('id', comment_id).execute()
        
        if not (hasattr(check_response, 'data') and check_response.data):
            raise HTTPException(status_code=404, detail="Comment không tồn tại")
        
        comment_owner = check_response.data[0].get('user_id')
        
        if comment_owner != user_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền sửa comment này")
        
        # Chuẩn bị data update
        update_data = {}
        if request.author_name is not None:
            update_data['author'] = request.author_name
        if request.rating is not None:
            update_data['rating'] = request.rating
        if request.text is not None:
            update_data['text'] = request.text
        
        if not update_data:
            raise HTTPException(status_code=400, detail="Không có dữ liệu để cập nhật")
        
        # Update comment
        response = db.table('comments').update(update_data).eq('id', comment_id).execute()
        
        if hasattr(response, 'data') and response.data:
            return APIResponse(
                success=True,
                message="Đã cập nhật comment thành công",
                data={"comment_id": comment_id}
            )
        else:
            raise HTTPException(status_code=500, detail="Lỗi khi cập nhật comment")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi cập nhật comment: {str(e)}")


@router.delete("/comments/{comment_id}", response_model=APIResponse)
async def delete_comment(
    comment_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_db)
):
    """
    Xóa comment (chỉ owner mới được xóa).
    Trigger `trigger_update_place_rating` sẽ tự động cập nhật rating của place.
    Requires JWT authentication.
    
    - **comment_id**: UUID của comment cần xóa
    """
    try:
        # Kiểm tra comment tồn tại và quyền sở hữu
        check_response = db.table('comments').select('user_id').eq('id', comment_id).execute()
        
        if not (hasattr(check_response, 'data') and check_response.data):
            raise HTTPException(status_code=404, detail="Comment không tồn tại")
        
        comment_owner = check_response.data[0].get('user_id')
        
        if comment_owner != user_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền xóa comment này")
        
        # Xóa comment - cascade sẽ xóa images liên quan (FK constraint)
        # Trigger sẽ tự động update rating của place
        response = db.table('comments').delete().eq('id', comment_id).execute()
        
        if hasattr(response, 'data'):
            return APIResponse(
                success=True,
                message="Đã xóa comment thành công"
            )
        else:
            raise HTTPException(status_code=500, detail="Lỗi khi xóa comment")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa comment: {str(e)}")


@router.post("/comments/{comment_id}/images", response_model=APIResponse)
async def add_images_to_comment(
    comment_id: str,
    request: AddImagesToCommentRequest,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_db)
):
    """
    Thêm ảnh vào comment đã có.
    Requires JWT authentication.
    
    - **comment_id**: UUID của comment
    - **image_urls**: Danh sách URLs ảnh (đã upload trước đó)
    """
    try:
        # Kiểm tra comment tồn tại và quyền sở hữu
        check_response = db.table('comments').select('user_id, place_id').eq('id', comment_id).execute()
        
        if not (hasattr(check_response, 'data') and check_response.data):
            raise HTTPException(status_code=404, detail="Comment không tồn tại")
        
        comment_data = check_response.data[0]
        comment_owner = comment_data.get('user_id')
        place_id = comment_data.get('place_id')
        
        if comment_owner != user_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền thêm ảnh vào comment này")
        
        # Insert images
        added_count = 0
        for url in request.image_urls:
            img_data = {
                "id": str(uuid.uuid4()),
                "comment_id": comment_id,
                "place_id": place_id,
                "url": url,
                "is_scraped": False,
                "uploaded_at": get_utc_now().isoformat()
            }
            result = db.table('images').insert(img_data).execute()
            if hasattr(result, 'data') and result.data:
                added_count += 1
        
        return APIResponse(
            success=True,
            message=f"Đã thêm {added_count} ảnh vào comment"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi thêm ảnh: {str(e)}")


@router.delete("/comments/{comment_id}/images/{image_id}", response_model=APIResponse)
async def delete_comment_image(
    comment_id: str,
    image_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_db)
):
    """
    Xóa một ảnh khỏi comment.
    Requires JWT authentication.
    
    - **comment_id**: UUID của comment
    - **image_id**: UUID của ảnh cần xóa
    """
    try:
        # Kiểm tra comment tồn tại và quyền sở hữu
        check_response = db.table('comments').select('user_id').eq('id', comment_id).execute()
        
        if not (hasattr(check_response, 'data') and check_response.data):
            raise HTTPException(status_code=404, detail="Comment không tồn tại")
        
        comment_owner = check_response.data[0].get('user_id')
        
        if comment_owner != user_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền xóa ảnh này")
        
        # Kiểm tra ảnh thuộc comment này
        img_check = db.table('images').select('id').eq('id', image_id).eq('comment_id', comment_id).execute()
        
        if not (hasattr(img_check, 'data') and img_check.data):
            raise HTTPException(status_code=404, detail="Ảnh không tồn tại hoặc không thuộc comment này")
        
        # Xóa ảnh
        db.table('images').delete().eq('id', image_id).execute()
        
        return APIResponse(success=True, message="Đã xóa ảnh thành công")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa ảnh: {str(e)}")
