# VietSpot API Documentation

> **Base URL:** `http://localhost:8000`  
> **API Prefix:** `/api`

---

## 📋 Mục lục

- [Health Check](#health-check)
- [Places](#places)
- [Comments](#comments)
- [Users](#users)
- [Images](#images)
- [Authentication](#authentication)
- [Database Triggers](#database-triggers)
- [RPC Functions](#rpc-functions)
- [Error Codes](#error-codes)
- [API Summary Table](#api-summary-table)

---

## Health Check

### GET /health

Kiểm tra trạng thái server.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "version": "1.0.0"
}
```

---

### GET /

Thông tin API.

**Response:**
```json
{
  "message": "Welcome to VietSpot API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

## Places

### 1. GET /api/places

Lấy danh sách địa điểm với filters (sử dụng RPC `get_places_advanced_v2`).

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | int | 0 | Số records bỏ qua |
| `limit` | int | 20 | Số records tối đa (1-100) |
| `lat` | float | null | Latitude của user |
| `lon` | float | null | Longitude của user |
| `max_distance` | int | null | Khoảng cách tối đa (km) |
| `location` | string | null | Tìm theo địa chỉ/thành phố |
| `categories` | string | null | Categories (phân cách bằng dấu phẩy) |
| `min_rating` | float | null | Rating tối thiểu (0-5) |
| `sort_by` | string | "rating" | Danh sách sort options (phân cách bằng dấu phẩy, VD: distance,rating,popularity) |

**Example:**
```
GET /api/places?lat=10.7769&lon=106.7009&max_distance=10&categories=Di%20Tích%20Lịch%20Sử&min_rating=4&sort_by=distance&limit=10
```

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Dinh Độc Lập",
    "address": "135 Nam Kỳ Khởi Nghĩa, Quận 1, TP.HCM",
    "phone": "028 3822 3652",
    "website": "https://dinhdoclap.gov.vn",
    "category": "Di Tích Lịch Sử",
    "rating": 4.6,
    "rating_count": 1250,
    "opening_hours": {...},
    "about": {...},
    "coordinates": [106.6955, 10.7769],
    "distance_km": 0.5,
    "distance_m": 500,
    "images": [
      {"id": "uuid", "url": "https://..."}
    ]
  }
]
```

---

### 2. GET /api/places/nearby

Lấy địa điểm gần vị trí user (sử dụng RPC `get_places_advanced_v2`).

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `lat` | float | ✅ Yes | - | Latitude của user |
| `lon` | float | ✅ Yes | - | Longitude của user |
| `radius` | int | No | 5 | Bán kính tìm kiếm (km, 1-50) |
| `categories` | string | No | null | Filter theo categories |
| `min_rating` | float | No | null | Rating tối thiểu |
| `limit` | int | No | 20 | Số kết quả tối đa |

**Example:**
```
GET /api/places/nearby?lat=10.7769&lon=106.7009&radius=5&limit=10
```

**Response:** Tương tự GET /api/places, tự động sort theo distance.

---

### 3. GET /api/places/categories

Lấy danh sách tất cả categories.

**Response:**
```json
[
  "Di Tích Lịch Sử",
  "Quán Cà Phê",
  "Nhà Hàng",
  "Công Viên",
  "Biển & Bãi Biển"
]
```

---

### 4. GET /api/places/{place_id}

Lấy chi tiết một địa điểm.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `place_id` | uuid | ID của địa điểm |

**Response:**
```json
{
  "id": "uuid",
  "name": "Dinh Độc Lập",
  "address": "135 Nam Kỳ Khởi Nghĩa, Quận 1, TP.HCM",
  "phone": "028 3822 3652",
  "website": "https://dinhdoclap.gov.vn",
  "category": "Di Tích Lịch Sử",
  "rating": 4.6,
  "rating_count": 1250,
  "opening_hours": {
    "Thứ Hai": "07:30-16:00",
    "Thứ Ba": "07:30-16:00"
  },
  "about": {
    "amenities": {"Nhà vệ sinh": true},
    "parking": {}
  },
  "coordinates": [106.6955, 10.7769],
  "images": [
    {"id": "uuid", "url": "https://..."}
  ],
  "comments": [...],
  "comments_count": 5
}
```

**Error Response (404):**
```json
{
  "detail": "Không tìm thấy địa điểm với id {place_id}"
}
```

---

### 5. POST /api/places

Tạo địa điểm mới.

**Request Body:**
```json
{
  "name": "Quán Cà Phê ABC",
  "address": "123 Nguyễn Huệ, Quận 1, TP.HCM",
  "phone": "0901234567",
  "website": "https://abc.com",
  "category": "Quán Cà Phê",
  "coordinates": {"lat": 10.7769, "lon": 106.7009},
  "opening_hours": {
    "monday": "08:00-22:00"
  },
  "about": {
    "price_level": 2
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ Yes | Tên địa điểm |
| `address` | string | No | Địa chỉ |
| `phone` | string | No | Số điện thoại |
| `website` | string | No | Website |
| `category` | string | No | Danh mục |
| `coordinates` | object | No | Tọa độ {lat, lon} |
| `opening_hours` | object | No | Giờ mở cửa |
| `about` | object | No | Thông tin thêm |

**Response (201):**
```json
{
  "id": "uuid",
  "name": "Quán Cà Phê ABC",
  "images": [],
  ...
}
```

---

### 6. PUT /api/places/{place_id}

Cập nhật địa điểm.

**Request Body:** (tất cả fields đều optional)
```json
{
  "name": "Tên mới",
  "address": "Địa chỉ mới",
  "phone": "0909876543"
}
```

**Response:** Place object đã cập nhật.

**Error Response (404):**
```json
{
  "detail": "Không tìm thấy địa điểm với id {place_id}"
}
```

---

### 7. DELETE /api/places/{place_id}

Xóa địa điểm.

> ⚠️ Trigger `trigger_delete_place_cascade` tự động xóa images và comments liên quan.

**Response:**
```json
{
  "message": "Đã xóa địa điểm thành công",
  "id": "uuid"
}
```

---

### 8. GET /api/places/{place_id}/images

Lấy danh sách ảnh của địa điểm.

**Response:**
```json
[
  {
    "id": "uuid",
    "url": "https://storage.supabase.co/...",
    "place_id": "uuid",
    "comment_id": null,
    "is_scraped": true,
    "uploaded_at": "2024-01-01T00:00:00"
  }
]
```

---

### 9. GET /api/places/{place_id}/comments

Lấy danh sách comments của địa điểm (sử dụng RPC `get_comments_by_place`).

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 20 | Số comments tối đa |
| `offset` | int | 0 | Số comments bỏ qua |
| `order_by` | string | "recent" | recent, rating_desc, rating_asc |

**Response:**
```json
[
  {
    "id": "uuid",
    "place_id": "uuid",
    "user_id": "uuid",
    "author": "Nguyễn Văn A",
    "rating": 5,
    "text": "Địa điểm rất đẹp!",
    "date": "2024-01-15",
    "is_scraped": false,
    "images": [
      {"id": "uuid", "url": "https://...", "is_scraped": false}
    ]
  }
]
```

---

## Comments

### 1. POST /api/comments

Tạo comment mới (sử dụng RPC `create_user_content`).

> ✅ Tự động tạo guest user nếu `user_id` không tồn tại trong database.

**Request Body:**
```json
{
  "place_id": "uuid",
  "user_id": "uuid",
  "author_name": "Nguyễn Văn A",
  "rating": 5,
  "text": "Địa điểm rất đẹp!",
  "image_urls": [
    "https://storage.supabase.co/bucket/image1.jpg"
  ]
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `place_id` | uuid | ✅ Yes | - | ID của địa điểm |
| `user_id` | uuid | No | auto-generate | ID của user |
| `author_name` | string | No | "Khách tham quan" | Tên hiển thị |
| `rating` | int | No | 5 | Điểm đánh giá (0-5) |
| `text` | string | No | null | Nội dung comment |
| `image_urls` | string[] | No | [] | URLs ảnh đã upload |

**Response:**
```json
{
  "success": true,
  "message": "Thành công",
  "data": {
    "comment_id": "uuid",
    "user_id": "uuid",
    "images_count": 1
  }
}
```

**Error Response (400):**
```json
{
  "detail": "Place ID không tồn tại"
}
```

---

### 2. PUT /api/comments/{comment_id}

Cập nhật comment (chỉ owner).

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `X-User-ID` | uuid | ✅ Yes | UUID của owner |

**Request Body:**
```json
{
  "author_name": "Tên mới",
  "rating": 4,
  "text": "Nội dung đã chỉnh sửa"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `author_name` | string | No | Tên hiển thị mới |
| `rating` | int | No | Điểm đánh giá mới (0-5) |
| `text` | string | No | Nội dung mới |

**Response:**
```json
{
  "success": true,
  "message": "Đã cập nhật comment thành công",
  "data": {
    "comment_id": "uuid"
  }
}
```

**Error Responses:**
- `403`: Bạn không có quyền sửa comment này
- `404`: Comment không tồn tại

---

### 3. DELETE /api/comments/{comment_id}

Xóa comment (chỉ owner).

> ⚠️ Trigger `trigger_update_place_rating` tự động cập nhật rating của place.

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `X-User-ID` | uuid | ✅ Yes | UUID của owner |

**Response:**
```json
{
  "success": true,
  "message": "Đã xóa comment thành công"
}
```

**Error Responses:**
- `403`: Bạn không có quyền xóa comment này
- `404`: Comment không tồn tại

---

### 4. POST /api/comments/{comment_id}/images

Thêm ảnh vào comment (chỉ owner).

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `X-User-ID` | uuid | ✅ Yes | UUID của owner |

**Request Body:**
```json
{
  "image_urls": [
    "https://storage.supabase.co/bucket/image1.jpg",
    "https://storage.supabase.co/bucket/image2.jpg"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Đã thêm 2 ảnh vào comment"
}
```

---

### 5. DELETE /api/comments/{comment_id}/images/{image_id}

Xóa ảnh khỏi comment (chỉ owner).

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `X-User-ID` | uuid | ✅ Yes | UUID của owner |

**Response:**
```json
{
  "success": true,
  "message": "Đã xóa ảnh thành công"
}
```

**Error Responses:**
- `403`: Bạn không có quyền xóa ảnh này
- `404`: Ảnh không tồn tại hoặc không thuộc comment này

---

## Users

### 1. GET /api/users/{user_id}/comments

Lấy tất cả comments của user.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 20 | Số comments tối đa |
| `offset` | int | 0 | Số comments bỏ qua |

**Response:**
```json
[
  {
    "id": "uuid",
    "place_id": "uuid",
    "rating": 5,
    "text": "Rất tuyệt!",
    "date": "2024-01-15",
    "author": "Nguyễn Văn A",
    "images": [...]
  }
]
```

---

### 2. GET /api/users/{user_id}/commented-places

Lấy danh sách places mà user đã comment.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 50 | Số places tối đa |
| `offset` | int | 0 | Số places bỏ qua |

**Response:**
```json
{
  "success": true,
  "count": 3,
  "places": [
    {
      "id": "uuid",
      "name": "Dinh Độc Lập",
      "address": "...",
      "category": "Di Tích Lịch Sử",
      "rating": 4.6
    }
  ]
}
```

---

## Images

### POST /api/upload

Upload ảnh lên Supabase Storage.

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `X-User-ID` | uuid | ✅ Yes | UUID của user |
| `Content-Type` | string | ✅ Yes | multipart/form-data |

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `files` | File[] | ✅ Yes | Files ảnh (tối đa 5 files) |

**Allowed file types:** jpg, jpeg, png, gif, webp

**Response:**
```json
{
  "success": true,
  "message": "Đã upload 3 ảnh",
  "urls": [
    "https://xxx.supabase.co/storage/v1/object/public/images/reviews/abc123.jpg",
    "https://xxx.supabase.co/storage/v1/object/public/images/reviews/def456.jpg"
  ]
}
```

**Error Responses:**
```json
{
  "detail": "Tối đa 5 ảnh mỗi lần upload"
}
```
```json
{
  "detail": "File type not allowed"
}
```

---

## Authentication

Hiện tại API sử dụng header `X-User-ID` để xác thực user.

### Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `X-User-ID` | uuid | Yes* | UUID của user (bắt buộc cho các endpoint cần xác thực) |

**Endpoints yêu cầu `X-User-ID`:**
- `PUT /api/comments/{comment_id}`
- `DELETE /api/comments/{comment_id}`
- `POST /api/comments/{comment_id}/images`
- `DELETE /api/comments/{comment_id}/images/{image_id}`
- `POST /api/upload`

---

## Database Triggers

| Trigger | Table | Events | Description |
|---------|-------|--------|-------------|
| `trigger_delete_place_cascade` | places | BEFORE DELETE | Tự động xóa images/comments khi xóa place |
| `trigger_update_place_rating` | comments | AFTER INSERT/UPDATE/DELETE | Tự động cập nhật rating của place |
| `trigger_sync_geom` | places | BEFORE INSERT/UPDATE | Sync PostGIS geometry từ coordinates |
| `set_places_geom_trigger` | places | BEFORE INSERT/UPDATE | Update geometry cho PostGIS queries |

---

## RPC Functions

### get_places_advanced_v2

Lấy places với PostGIS distance calculation.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `p_location` | text | Filter theo địa chỉ |
| `p_lat` | double precision | Latitude của user |
| `p_lon` | double precision | Longitude của user |
| `p_categories` | text[] | Array của categories |
| `p_min_rating` | double precision | Rating tối thiểu |
| `p_max_distance` | integer | Khoảng cách tối đa (km) |
| `p_price_levels` | integer[] | Các mức giá |
| `p_amenities_jsonb` | jsonb | Filter amenities |
| `p_sort_options` | text[] | Array sort options |
| `p_limit` | integer | Số kết quả tối đa |

---

### get_comments_by_place

Lấy comments với images.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `p_place_id` | uuid | ID của địa điểm |
| `p_limit` | integer | Số comments tối đa |
| `p_offset` | integer | Số comments bỏ qua |
| `p_order_by` | text | recent, rating_desc, rating_asc |

---

### create_user_content

Tạo comment + auto tạo guest user + insert images.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `p_place_id` | uuid | ID của địa điểm |
| `p_user_id` | uuid | ID của user |
| `p_author_name` | text | Tên hiển thị |
| `p_rating` | integer | Điểm đánh giá |
| `p_text` | text | Nội dung comment |
| `p_image_urls` | text[] | URLs của ảnh |

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Dữ liệu không hợp lệ |
| 403 | Forbidden - Không có quyền |
| 404 | Not Found - Không tìm thấy resource |
| 422 | Validation Error - Lỗi validate input |
| 500 | Internal Server Error - Lỗi server |

**Error Response Format:**
```json
{
  "detail": "Mô tả lỗi chi tiết"
}
```

---

## API Summary Table

| # | Method | Endpoint | Auth | Description |
|---|--------|----------|------|-------------|
| 1 | GET | `/health` | No | Health check |
| 2 | GET | `/` | No | API info |
| 3 | GET | `/api/places` | No | Lấy danh sách places |
| 4 | GET | `/api/places/nearby` | No | Lấy places gần đây |
| 5 | GET | `/api/places/categories` | No | Lấy danh sách categories |
| 6 | GET | `/api/places/{id}` | No | Lấy chi tiết place |
| 7 | POST | `/api/places` | No | Tạo place mới |
| 8 | PUT | `/api/places/{id}` | No | Cập nhật place |
| 9 | DELETE | `/api/places/{id}` | No | Xóa place |
| 10 | GET | `/api/places/{id}/images` | No | Lấy ảnh của place |
| 11 | GET | `/api/places/{id}/comments` | No | Lấy comments của place |
| 12 | POST | `/api/comments` | No | Tạo comment |
| 13 | PUT | `/api/comments/{id}` | **X-User-ID** | Cập nhật comment |
| 14 | DELETE | `/api/comments/{id}` | **X-User-ID** | Xóa comment |
| 15 | POST | `/api/comments/{id}/images` | **X-User-ID** | Thêm ảnh vào comment |
| 16 | DELETE | `/api/comments/{id}/images/{img_id}` | **X-User-ID** | Xóa ảnh khỏi comment |
| 17 | GET | `/api/users/{id}/comments` | No | Lấy comments của user |
| 18 | GET | `/api/users/{id}/commented-places` | No | Lấy places user đã comment |
| 19 | POST | `/api/upload` | **X-User-ID** | Upload ảnh |

---

## Notes

1. **Images Workflow**: Upload ảnh trước qua `/api/upload`, sau đó dùng URLs trả về khi tạo/update comment.

2. **Distance Calculation**: Khi truyền `lat`, `lon`, API sẽ tính `distance_km` cho mỗi place sử dụng PostGIS.

3. **Guest User**: Khi tạo comment mà `user_id` không tồn tại, RPC sẽ tự động tạo guest user.

4. **Coordinates Format**: Database lưu coordinates dạng GeoJSON `[lon, lat]` array.

5. **Rating Auto-Update**: Khi thêm/sửa/xóa comment, trigger sẽ tự động cập nhật rating trung bình của place.
