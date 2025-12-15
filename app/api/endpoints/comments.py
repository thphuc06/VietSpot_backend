"""
Comments Endpoints
Xử lý các API liên quan đến comments/reviews
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from supabase import Client
from datetime import datetime
import uuid

from app.api.deps import get_user_id_from_header, get_db
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
    """
    Lấy danh sách comments của một địa điểm.
    
    - **place_id**: UUID của địa điểm
    - **limit**: Số lượng comments tối đa (default: 20)
    - **offset**: Vị trí bắt đầu (default: 0)
    - **order_by**: Cách sắp xếp (recent, rating_desc, rating_asc)
    """
    try:
        query = db.table('comments').select('*').eq('place_id', place_id)
        
        # Áp dụng sorting
        if order_by == "recent":
            query = query.order('date', desc=True)
        elif order_by == "rating_desc":
            query = query.order('rating', desc=True)
        elif order_by == "rating_asc":
            query = query.order('rating', desc=False)
        
        # Áp dụng pagination
        query = query.range(offset, offset + limit - 1)
        
        response = query.execute()
        
        if hasattr(response, 'data'):
            comments = response.data
            
            # Lấy ảnh cho từng comment
            for comment in comments:
                comment_id = comment.get('id')
                img_response = db.table('images').select('*').eq('comment_id', comment_id).execute()
                
                if hasattr(img_response, 'data') and img_response.data:
                    comment['images'] = img_response.data
                else:
                    comment['images'] = []
            
            return comments
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy comments: {str(e)}")


@router.post("/comments", response_model=APIResponse)
async def create_comment(
    request: CreateCommentRequest,
    db: Client = Depends(get_db)
):
    """
    Tạo comment mới cho một địa điểm.
    
    Body:
    - **place_id**: UUID của địa điểm
    - **user_id**: UUID của user (optional - có thể để trống cho khách)
    - **author_name**: Tên hiển thị
    - **rating**: Điểm đánh giá (0-5)
    - **text**: Nội dung comment
    - **image_urls**: Danh sách URLs ảnh (đã upload trước đó)
    """
    try:
        # Validate place_id tồn tại
        place_check = db.table('places').select('id').eq('id', request.place_id).execute()
        if not (hasattr(place_check, 'data') and place_check.data):
            raise HTTPException(status_code=404, detail="Địa điểm không tồn tại")
        
        # Validate user_id nếu có
        user_id_to_use = None
        if request.user_id and request.user_id.strip():
            user_check = db.table('users').select('id').eq('id', request.user_id).execute()
            if not (hasattr(user_check, 'data') and user_check.data):
                raise HTTPException(status_code=404, detail="User không tồn tại")
            user_id_to_use = request.user_id
        
        # Insert comment trực tiếp
        comment_id = str(uuid.uuid4())
        
        comment_data = {
            "id": comment_id,
            "place_id": request.place_id,
            "author": request.author_name,
            "rating": request.rating,
            "text": request.text,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "is_scraped": False
        }
        
        # Chỉ thêm user_id nếu có
        if user_id_to_use:
            comment_data["user_id"] = user_id_to_use
        
        comment_response = db.table('comments').insert(comment_data).execute()
        
        if not (hasattr(comment_response, 'data') and comment_response.data):
            raise HTTPException(status_code=500, detail="Lỗi khi tạo comment")
        
        # Insert images nếu có
        if request.image_urls:
            for url in request.image_urls:
                if url and url.strip():
                    img_data = {
                        "id": str(uuid.uuid4()),
                        "comment_id": comment_id,
                        "place_id": request.place_id,
                        "url": url,
                        "is_scraped": False,
                        "uploaded_at": datetime.now().isoformat()
                    }
                    db.table('images').insert(img_data).execute()
        
        return APIResponse(
            success=True,
            message="Đã tạo comment thành công",
            data={"comment_id": comment_id}
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo comment: {str(e)}")


@router.put("/comments/{comment_id}", response_model=APIResponse)
async def update_comment(
    comment_id: str,
    request: UpdateCommentRequest,
    user_id: str = Depends(get_user_id_from_header),
    db: Client = Depends(get_db)
):
    """
    Chỉnh sửa comment (chỉ owner mới được sửa).
    
    - **comment_id**: UUID của comment cần sửa
    - **X-User-ID**: Header chứa user_id
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
    user_id: str = Depends(get_user_id_from_header),
    db: Client = Depends(get_db)
):
    """
    Xóa comment (chỉ owner mới được xóa).
    
    - **comment_id**: UUID của comment cần xóa
    - **X-User-ID**: Header chứa user_id
    """
    try:
        # Kiểm tra comment tồn tại và quyền sở hữu
        check_response = db.table('comments').select('user_id').eq('id', comment_id).execute()
        
        if not (hasattr(check_response, 'data') and check_response.data):
            raise HTTPException(status_code=404, detail="Comment không tồn tại")
        
        comment_owner = check_response.data[0].get('user_id')
        
        if comment_owner != user_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền xóa comment này")
        
        # Xóa ảnh liên quan trước
        db.table('images').delete().eq('comment_id', comment_id).execute()
        
        # Xóa comment
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
    user_id: str = Depends(get_user_id_from_header),
    db: Client = Depends(get_db)
):
    """
    Thêm ảnh vào comment đã có.
    
    - **comment_id**: UUID của comment
    - **image_urls**: Danh sách URLs ảnh (đã upload trước đó)
    - **X-User-ID**: Header chứa user_id
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
                "uploaded_at": datetime.now().isoformat()
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
    user_id: str = Depends(get_user_id_from_header),
    db: Client = Depends(get_db)
):
    """
    Xóa một ảnh khỏi comment.
    
    - **comment_id**: UUID của comment
    - **image_id**: UUID của ảnh cần xóa
    - **X-User-ID**: Header chứa user_id
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
