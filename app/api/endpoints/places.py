"""
Places Endpoints
Xử lý các API liên quan đến địa điểm du lịch
"""

import math
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from supabase import Client

from app.api.deps import get_db
from app.schemas.place import Place, PlaceCreate, PlaceUpdate

router = APIRouter()


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Tính khoảng cách giữa 2 điểm (Haversine formula).
    Trả về khoảng cách tính bằng km.
    """
    R = 6371  # Bán kính trái đất (km)
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return round(R * c, 2)


def get_place_coordinates(place: dict) -> tuple:
    """
    Lấy lat, lon từ place coordinates.
    Xử lý nhiều format khác nhau của coordinates.
    
    Returns: (lat, lon) hoặc (None, None)
    """
    coords = place.get("coordinates")
    if not coords:
        return None, None
    
    # Nếu coords là string, parse JSON
    if isinstance(coords, str):
        import json
        try:
            coords = json.loads(coords)
        except:
            return None, None
    
    # Format 1: Array [lon, lat] (GeoJSON standard)
    if isinstance(coords, list) and len(coords) >= 2:
        try:
            lon = float(coords[0])
            lat = float(coords[1])
            return lat, lon
        except:
            return None, None
    
    # Format 2: Object {lat: ..., lon/lng: ...}
    if isinstance(coords, dict):
        lat = coords.get("lat") or coords.get("latitude")
        lon = coords.get("lon") or coords.get("lng") or coords.get("longitude")
        
        if lat is not None and lon is not None:
            try:
                return float(lat), float(lon)
            except:
                return None, None
    
    return None, None


@router.get("", response_model=List[dict])
async def get_places(
    # Pagination
    skip: int = Query(0, ge=0, description="Số records bỏ qua"),
    limit: int = Query(20, ge=1, le=100, description="Số records tối đa"),
    
    # Location filters
    lat: Optional[float] = Query(None, description="Latitude của user (để tính khoảng cách)"),
    lon: Optional[float] = Query(None, description="Longitude của user (để tính khoảng cách)"),
    max_distance: Optional[int] = Query(None, description="Khoảng cách tối đa (km)"),
    location: Optional[str] = Query(None, description="Tìm theo địa điểm/thành phố trong address"),
    
    # Category & Rating filters  
    categories: Optional[str] = Query(None, description="Categories (phân cách bằng dấu phẩy, VD: 'Quán cà phê,Nhà hàng')"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Rating tối thiểu"),
    
    # Search
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên"),
    
    # Sort
    sort_by: Optional[str] = Query("rating", description="Sắp xếp: rating, distance, rating_count"),
    
    db: Client = Depends(get_db)
):
    """
    Lấy danh sách các địa điểm với đầy đủ filters.
    
    - **lat, lon**: Tọa độ user để tính khoảng cách và sắp xếp theo distance
    - **max_distance**: Lọc địa điểm trong bán kính (km)
    - **location**: Tìm theo thành phố/địa chỉ
    - **categories**: Lọc theo loại địa điểm (phân cách bằng dấu phẩy)
    - **min_rating**: Lọc rating tối thiểu
    - **search**: Tìm kiếm theo tên
    - **sort_by**: Sắp xếp theo rating/distance/rating_count
    """
    try:
        # Parse categories từ string thành list
        category_list = None
        if categories:
            category_list = [c.strip() for c in categories.split(",") if c.strip()]
        
        # Query database - lấy nhiều để filter distance sau
        query = db.table("places").select("*")
        
        # Filter theo categories
        if category_list and len(category_list) > 0:
            if len(category_list) == 1:
                query = query.eq("category", category_list[0])
            else:
                query = query.in_("category", category_list)
        
        # Filter theo location (tìm trong address)
        if location:
            query = query.ilike("address", f"%{location}%")
        
        # Filter theo rating
        if min_rating is not None and min_rating > 0:
            query = query.gte("rating", min_rating)
        
        # Tìm kiếm theo tên
        if search:
            query = query.ilike("name", f"%{search}%")
        
        # Sắp xếp theo rating trước
        query = query.order("rating", desc=True)
        
        # Nếu cần filter distance, lấy nhiều records hơn
        # Vì filter distance xảy ra ở code Python, không phải DB
        if lat is not None and lon is not None and max_distance is not None:
            fetch_limit = 1000  # Lấy nhiều để filter
        else:
            fetch_limit = skip + limit + 100  # Thêm buffer
        
        query = query.limit(fetch_limit)
        
        response = query.execute()
        places = response.data if response.data else []
        
        # ===== XỬ LÝ DISTANCE =====
        result_places = []
        
        for place in places:
            place_lat, place_lon = get_place_coordinates(place)
            
            # Tính khoảng cách nếu có tọa độ user
            if lat is not None and lon is not None:
                if place_lat is not None and place_lon is not None:
                    distance = calculate_distance(lat, lon, place_lat, place_lon)
                    place["distance_km"] = distance
                    place["distance_m"] = int(distance * 1000)
                    
                    # Filter theo max_distance - BỎ QUA place quá xa
                    if max_distance is not None and distance > max_distance:
                        continue  # Skip place này
                else:
                    # Place không có tọa độ
                    place["distance_km"] = None
                    place["distance_m"] = None
                    
                    # Nếu yêu cầu filter distance nhưng place không có tọa độ -> bỏ qua
                    if max_distance is not None:
                        continue
            else:
                # User không cung cấp tọa độ
                place["distance_km"] = None
                place["distance_m"] = None
            
            result_places.append(place)
        
        # ===== SORT =====
        if sort_by == "distance" and lat is not None and lon is not None:
            # Sort theo distance (gần nhất trước)
            result_places = sorted(
                result_places,
                key=lambda x: x.get("distance_km") if x.get("distance_km") is not None else 99999
            )
        elif sort_by == "rating_count":
            result_places = sorted(
                result_places,
                key=lambda x: x.get("rating_count") or 0,
                reverse=True
            )
        # Mặc định đã sort theo rating từ query
        
        # ===== PAGINATION (sau khi filter distance) =====
        result_places = result_places[skip:skip + limit]
        
        # ===== LẤY IMAGES =====
        for place in result_places:
            try:
                img_response = db.table("images").select("id, url").eq("place_id", place["id"]).limit(5).execute()
                place["images"] = img_response.data if img_response.data else []
            except:
                place["images"] = []
        
        return result_places
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy danh sách địa điểm: {str(e)}"
        )


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
    """
    Lấy các địa điểm gần vị trí user.
    Tự động sort theo khoảng cách (gần nhất trước).
    """
    return await get_places(
        skip=0,
        limit=limit,
        lat=lat,
        lon=lon,
        max_distance=radius,
        location=None,
        categories=categories,
        min_rating=min_rating,
        search=None,
        sort_by="distance",
        db=db
    )


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
    Xóa địa điểm (và các comments, images liên quan).
    
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
        
        # Xóa images liên quan
        db.table('images').delete().eq('place_id', place_id).execute()
        
        # Xóa comments liên quan
        db.table('comments').delete().eq('place_id', place_id).execute()
        
        # Delete place
        db.table('places').delete().eq('id', place_id).execute()
        
        return {"message": "Đã xóa địa điểm thành công", "id": place_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xóa địa điểm: {str(e)}"
        )
