"""
Users Endpoints
Xử lý các API liên quan đến user
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from supabase import Client

from app.api.deps import get_db
from app.schemas.comment import CommentResponse
from app.schemas.user import UserCommentedPlacesResponse

router = APIRouter()


@router.get("/{user_id}/comments", response_model=List[CommentResponse])
async def get_user_comments(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    db: Client = Depends(get_db)
):
    """
    Lấy danh sách tất cả comments của một user.
    (Để user xem lại các places đã comment)
    
    - **user_id**: UUID của user
    - **limit**: Số lượng comments tối đa
    - **offset**: Vị trí bắt đầu
    """
    try:
        query = db.table('comments').select('*, places(id, name, address, category)').eq('user_id', user_id)
        query = query.order('date', desc=True)
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
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy comments của user: {str(e)}")


@router.get("/{user_id}/commented-places", response_model=UserCommentedPlacesResponse)
async def get_user_commented_places(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Client = Depends(get_db)
):
    """
    Lấy danh sách các places mà user đã comment.
    (Để hiển thị trên profile của user)
    
    - **user_id**: UUID của user
    """
    try:
        # Lấy distinct place_ids từ comments của user
        response = db.table('comments').select(
            'place_id, places(id, name, address, category, rating, coordinates)'
        ).eq('user_id', user_id).execute()
        
        if hasattr(response, 'data'):
            # Group by place_id để loại bỏ trùng lặp
            places_dict = {}
            for comment in response.data:
                place_id = comment.get('place_id')
                place_info = comment.get('places')
                
                if place_id and place_info and place_id not in places_dict:
                    places_dict[place_id] = place_info
            
            return UserCommentedPlacesResponse(
                success=True,
                count=len(places_dict),
                places=list(places_dict.values())
            )
        
        return UserCommentedPlacesResponse(success=True, count=0, places=[])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy places đã comment: {str(e)}")
