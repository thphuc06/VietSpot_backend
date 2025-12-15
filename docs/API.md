# VietSpot API Documentation

> **Base URL:** `http://localhost:8000/api`

---

## 📋 Mục lục

- [Authentication](#authentication)
- [Images](#images)
- [Comments](#comments)
- [Users](#users)
- [Places](#places)
- [Health Check](#health-check)

---

## Authentication

Hiện tại API sử dụng header `X-User-ID` để xác thực user. Trong tương lai sẽ chuyển sang JWT token.

### Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `X-User-ID` | string | Yes* | UUID của user (bắt buộc cho các endpoint cần xác thực) |

---

## Images

### 1. Lấy ảnh của địa điểm

```http
GET /api/images/places/{place_id}/images
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `place_id` | string | Yes | UUID của địa điểm |

**Response:**

```json
[
  {
    "id": "uuid",
    "url": "https://...",
    "place_id": "uuid",
    "comment_id": null,
    "is_scraped": true,
    "uploaded_at": "2024-01-01T00:00:00"
  }
]
```

---

### 2. Lấy ảnh của comment

```http
GET /api/images/comments/{comment_id}/images
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `comment_id` | string | Yes | UUID của comment |

**Response:**

```json
[
  {
    "id": "uuid",
    "url": "https://...",
    "place_id": "uuid",
    "comment_id": "uuid",
    "is_scraped": false,
    "uploaded_at": "2024-01-01T00:00:00"
  }
]
```

---

### 3. Upload ảnh

```http
POST /api/images/upload
```

**Headers:**

| Header | Type | Required |
|--------|------|----------|
| `X-User-ID` | string | Yes |
| `Content-Type` | multipart/form-data | Yes |

**Body (form-data):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `files` | File[] | Yes | Danh sách file ảnh (tối đa 5 file) |

**Response:**

```json
{
  "success": true,
  "message": "Đã upload 3 ảnh",
  "urls": [
    "https://xxx.supabase.co/storage/v1/object/public/images/reviews/...",
    "https://xxx.supabase.co/storage/v1/object/public/images/reviews/...",
    "https://xxx.supabase.co/storage/v1/object/public/images/reviews/..."
  ]
}
```

**Error Response:**

```json
{
  "detail": "Tối đa 5 ảnh mỗi lần upload"
}
```

---

## Comments

### 1. Lấy comments của địa điểm

```http
GET /api/comments/places/{place_id}/comments
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `place_id` | string | Yes | - | UUID của địa điểm |
| `limit` | int | No | 20 | Số lượng comments tối đa |
| `offset` | int | No | 0 | Vị trí bắt đầu |
| `order_by` | string | No | "recent" | Cách sắp xếp: `recent`, `rating_desc`, `rating_asc` |

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
    "images": [
      {
        "id": "uuid",
        "url": "https://...",
        "place_id": "uuid",
        "comment_id": "uuid",
        "is_scraped": false,
        "uploaded_at": "2024-01-15T10:30:00"
      }
    ]
  }
]
```

---

### 2. Tạo comment mới

```http
POST /api/comments
```

**Body:**

```json
{
  "place_id": "uuid",
  "user_id": "uuid",
  "author_name": "Nguyễn Văn A",
  "rating": 5,
  "text": "Địa điểm rất đẹp, phong cảnh tuyệt vời!",
  "image_urls": [
    "https://xxx.supabase.co/storage/v1/object/public/images/reviews/..."
  ]
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `place_id` | string | Yes | - | UUID của địa điểm |
| `user_id` | string | Yes | - | UUID của user |
| `author_name` | string | No | "Khách tham quan" | Tên hiển thị |
| `rating` | int | No | 5 | Điểm đánh giá (0-5) |
| `text` | string | No | null | Nội dung comment |
| `image_urls` | string[] | No | [] | URLs ảnh đã upload |

**Response:**

```json
{
  "success": true,
  "message": "Đã tạo comment thành công",
  "data": {
    "comment_id": "uuid"
  }
}
```

---

### 3. Cập nhật comment

```http
PUT /api/comments/{comment_id}
```

**Headers:**

| Header | Type | Required |
|--------|------|----------|
| `X-User-ID` | string | Yes |

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `comment_id` | string | Yes | UUID của comment cần sửa |

**Body:**

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

**Error Response:**

```json
{
  "success": false,
  "message": "Bạn không có quyền sửa comment này"
}
```

---

### 4. Xóa comment

```http
DELETE /api/comments/{comment_id}
```

**Headers:**

| Header | Type | Required |
|--------|------|----------|
| `X-User-ID` | string | Yes |

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `comment_id` | string | Yes | UUID của comment cần xóa |

**Response:**

```json
{
  "success": true,
  "message": "Đã xóa comment thành công",
  "data": null
}
```

---

### 5. Thêm ảnh vào comment

```http
POST /api/comments/{comment_id}/images
```

**Headers:**

| Header | Type | Required |
|--------|------|----------|
| `X-User-ID` | string | Yes |

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `comment_id` | string | Yes | UUID của comment |

**Body:**

```json
{
  "image_urls": [
    "https://xxx.supabase.co/storage/v1/object/public/images/reviews/..."
  ]
}
```

**Response:**

```json
{
  "success": true,
  "message": "Đã thêm 2 ảnh vào comment",
  "data": null
}
```

---

### 6. Xóa ảnh khỏi comment

```http
DELETE /api/comments/{comment_id}/images/{image_id}
```

**Headers:**

| Header | Type | Required |
|--------|------|----------|
| `X-User-ID` | string | Yes |

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `comment_id` | string | Yes | UUID của comment |
| `image_id` | string | Yes | UUID của ảnh cần xóa |

**Response:**

```json
{
  "success": true,
  "message": "Đã xóa ảnh thành công",
  "data": null
}
```

---

## Users

### 1. Lấy comments của user

```http
GET /api/users/{user_id}/comments
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `user_id` | string | Yes | - | UUID của user |
| `limit` | int | No | 20 | Số lượng comments tối đa |
| `offset` | int | No | 0 | Vị trí bắt đầu |

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
    "images": [],
    "places": {
      "id": "uuid",
      "name": "Hồ Gươm",
      "address": "Hoàn Kiếm, Hà Nội",
      "category": "Thắng cảnh"
    }
  }
]
```

---

### 2. Lấy danh sách places đã comment

```http
GET /api/users/{user_id}/commented-places
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `user_id` | string | Yes | - | UUID của user |
| `limit` | int | No | 50 | Số lượng places tối đa |
| `offset` | int | No | 0 | Vị trí bắt đầu |

**Response:**

```json
{
  "success": true,
  "count": 5,
  "places": [
    {
      "id": "uuid",
      "name": "Hồ Gươm",
      "address": "Hoàn Kiếm, Hà Nội",
      "category": "Thắng cảnh",
      "rating": 4.5,
      "coordinates": {
        "lat": 21.0285,
        "lng": 105.8542
      }
    }
  ]
}
```

---

## Places

### 1. Lấy danh sách places

```http
GET /api/places
```

*(Endpoint này có sẵn trong places.py)*

---

## Health Check

### Kiểm tra trạng thái API

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "version": "1.0.0"
}
```

---

## Error Responses

### Standard Error Format

```json
{
  "detail": "Error message here"
}
```

### Common HTTP Status Codes

| Status | Description |
|--------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing X-User-ID header |
| 403 | Forbidden - No permission |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## Examples

### Workflow: Tạo comment với ảnh

**Bước 1: Upload ảnh trước**

```bash
curl -X POST "http://localhost:8000/api/images/upload" \
  -H "X-User-ID: user-uuid-here" \
  -F "files=@photo1.jpg" \
  -F "files=@photo2.jpg"
```

Response:
```json
{
  "success": true,
  "urls": ["https://...url1", "https://...url2"]
}
```

**Bước 2: Tạo comment với URLs ảnh**

```bash
curl -X POST "http://localhost:8000/api/comments" \
  -H "Content-Type: application/json" \
  -d '{
    "place_id": "place-uuid",
    "user_id": "user-uuid",
    "author_name": "Nguyễn Văn A",
    "rating": 5,
    "text": "Địa điểm tuyệt vời!",
    "image_urls": ["https://...url1", "https://...url2"]
  }'
```

---

## Rate Limiting

*(Chưa implement)*

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-15 | Initial release |
