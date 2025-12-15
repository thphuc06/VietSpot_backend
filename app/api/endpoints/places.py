"""
Places Endpoints
Xử lý các API liên quan đến địa điểm du lịch
Sử dụng RPC function get_places_advanced_v2 (PostGIS)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from supabase import Client

from app.api.deps import get_db
from app.schemas.place import Place, PlaceCreate, PlaceUpdate

router = APIRouter()


@router.get("", response_model=List[dict])
async def get_places(
    skip: int = Query(0, ge=0, description="Số records bỏ qua"),
    limit: int = Query(20, ge=1, le=100, description="Số records tối đa"),
    lat: Optional[float] = Query(None, description="Latitude của user"),
    lon: Optional[float] = Query(None, description="Longitude của user"),
    max_distance: Optional[int] = Query(None, description="Khoảng cách tối đa (km)"),
    location: Optional[str] = Query(None, description="Tìm theo địa điểm/thành phố"),
    categories: Optional[str] = Query(None, description="Categories (phân cách bằng dấu phẩy)"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Rating tối thiểu"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên"),
    sort_by: Optional[str] = Query("rating", description="Sắp xếp: rating, distance, popularity"),
    db: Client = Depends(get_db)
):
    """Lấy danh sách địa điểm với filters. Sử dụng RPC get_places_advanced_v2."""
    try:
        # Parse categories string thành array
        category_array = None
        if categories:
            category_array = [c.strip() for c in categories.split(",") if c.strip()]
        
        # sort_options phải là array
        sort_options_array = [s.strip() for s in sort_by.split(",")] if sort_by else ["rating"]
        
        # Gọi RPC function
        response = db.rpc("get_places_advanced_v2", {
            "p_location": location,
            "p_lat": lat,
            "p_lon": lon,
            "p_categories": category_array,
            "p_min_rating": min_rating,
            "p_max_distance": max_distance,
            "p_price_levels": None,
            "p_amenities_jsonb": None,
            "p_sort_options": sort_options_array,
            "p_limit": skip + limit + 50
        }).execute()
        
        places = response.data if response.data else []
        
        # Filter theo search (nếu RPC chưa support)
        if search:
            search_lower = search.lower()
            places = [p for p in places if search_lower in (p.get("name") or "").lower()]
        
        # Pagination
        places = places[skip:skip + limit]
        
        # Format output
        for place in places:
            if place.get("distance_km") is not None:
                place["distance_m"] = int(float(place["distance_km"]) * 1000)
            else:
                place["distance_m"] = None
            
            if "images" not in place or place["images"] is None:
                place["images"] = []
        
        return places
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy danh sách địa điểm: {str(e)}")


@router.get("/nearby", response_model=List[dict])
async def get_nearby_places(
    lat: float = Query(..., description="Latitude của user"),
    lon: float = Query(..., description="Longitude của user"),
    radius: int = Query(5, ge=1, le=50, description="Bán kính tìm kiếm (km)"),
    categories: Optional[str] = Query(None, description="Categories (phân cách bằng dấu phẩy)"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Rating tối thiểu"),
    limit: int = Query(20, ge=1, le=100, description="Số kết quả tối đa"),
    db: Client = Depends(get_db)
):
    """Lấy các địa điểm gần vị trí user, sort theo distance."""
    try:
        category_array = [c.strip() for c in categories.split(",") if c.strip()] if categories else None
        
        response = db.rpc("get_places_advanced_v2", {
            "p_location": None,
            "p_lat": lat,
            "p_lon": lon,
            "p_categories": category_array,
            "p_min_rating": min_rating,
            "p_max_distance": radius,
            "p_price_levels": None,
            "p_amenities_jsonb": None,
            "p_sort_options": ["distance"],
            "p_limit": limit
        }).execute()
        
        places = response.data if response.data else []
        
        for place in places:
            if place.get("distance_km") is not None:
                place["distance_m"] = int(float(place["distance_km"]) * 1000)
            else:
                place["distance_m"] = None
            if "images" not in place or place["images"] is None:
                place["images"] = []
        
        return places
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


@router.get("/categories", response_model=List[str])
async def get_categories(
    db: Client = Depends(get_db)
):
    """Lấy danh sách tất cả categories có trong database"""
    try:
        response = db.table("places").select("category").not_.is_("category", "null").execute()
        
        if response.data:
            # Lấy unique categories
            categories = list(set(item["category"] for item in response.data if item.get("category")))
            categories.sort()
            return categories
        
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


# Debug endpoint đã được remove vì lý do bảo mật
# Nếu cần debug, có thể enable lại trong môi trường development


@router.get("/{place_id}")
async def get_place(
    place_id: str,
    db: Client = Depends(get_db)
):
    """
    Lấy thông tin chi tiết một địa điểm.
    
    - **place_id**: UUID của địa điểm
    """
    try:
        response = db.table('places').select('*').eq('id', place_id).execute()
        
        if response.data:
            place = response.data[0]
            
            # Lấy images của place
            img_resp = db.table('images').select('id, url').eq('place_id', place_id).execute()
            place['images'] = img_resp.data if img_resp.data else []
            
            # Lấy comments
            comments_resp = db.table('comments').select('*').eq('place_id', place_id).order('date', desc=True).execute()
            place['comments'] = comments_resp.data if comments_resp.data else []
            place['comments_count'] = len(place['comments'])
            
            return place
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy địa điểm với id {place_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy thông tin địa điểm: {str(e)}"
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_place(
    place_in: PlaceCreate,
    db: Client = Depends(get_db)
):
    """
    Tạo địa điểm mới.
    
    Body:
    - **name**: Tên địa điểm (bắt buộc)
    - **address**: Địa chỉ
    - **phone**: Số điện thoại
    - **website**: Website
    - **category**: Danh mục
    - **coordinates**: Tọa độ {lat, lon}
    """
    try:
        place_data = place_in.model_dump(exclude_none=True)
        place_data['is_scraped'] = False
        
        response = db.table('places').insert(place_data).execute()
        
        if response.data:
            created = response.data[0]
            created['images'] = []
            return created
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể tạo địa điểm"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tạo địa điểm: {str(e)}"
        )


@router.put("/{place_id}")
async def update_place(
    place_id: str,
    place_in: PlaceUpdate,
    db: Client = Depends(get_db)
):
    """
    Cập nhật thông tin địa điểm.
    
    - **place_id**: UUID của địa điểm
    """
    try:
        # Check if place exists
        check = db.table('places').select('id').eq('id', place_id).execute()
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy địa điểm với id {place_id}"
            )
        
        # Update place - chỉ lấy các field không None
        update_data = place_in.model_dump(exclude_none=True)
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không có dữ liệu để cập nhật"
            )
        
        response = db.table('places').update(update_data).eq('id', place_id).execute()
        
        if response.data:
            return response.data[0]
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể cập nhật địa điểm"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi cập nhật địa điểm: {str(e)}"
        )


@router.delete("/{place_id}")
async def delete_place(
    place_id: str,
    db: Client = Depends(get_db)
):
    """
    Xóa địa điểm.
    Trigger `trigger_delete_place_cascade` sẽ tự động xóa images/comments liên quan.
    
    - **place_id**: UUID của địa điểm
    """
    try:
        # Check if place exists
        check = db.table('places').select('id').eq('id', place_id).execute()
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy địa điểm với id {place_id}"
            )
        
        # Delete place - trigger sẽ cascade delete images và comments
        db.table('places').delete().eq('id', place_id).execute()
        
        return {"message": "Đã xóa địa điểm thành công", "id": place_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xóa địa điểm: {str(e)}"
        )
