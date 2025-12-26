# VietSpot API Documentation

> **Base URL:** `http://localhost:8000`  
> **API Prefix:** `/api`
> **Backend Deploy URL:** `https://vietspotbackend-production.up.railway.app/docs`

---

## 📋 Mục lục

- [Health Check](#health-check)
- [Places](#places)
- [Comments](#comments)
- [Users](#users)
- [Images](#images)
- [Chat (AI Chatbot)](#chat-ai-chatbot)
- [Itinerary](#itinerary)
- [Text-to-Speech](#text-to-speech)
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

### 4. GET /api/places/search

Tìm kiếm địa điểm theo tên sử dụng fuzzy search (similarity >= 50%).

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `keyword` | string | ✅ Yes | - | Từ khóa tìm kiếm (tên địa điểm) |
| `lat` | float | No | null | Latitude của user (optional, để sắp xếp theo khoảng cách) |
| `lon` | float | No | null | Longitude của user (optional) |
| `limit` | int | No | 20 | Số kết quả tối đa (1-100) |

**Example:**
```
GET /api/places/search?keyword=Dinh%20Độc%20Lập&lat=10.7769&lon=106.7009&limit=10
```

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Dinh Độc Lập",
    "address": "135 Nam Kỳ Khởi Nghĩa, Quận 1, TP.HCM",
    "category": "Di Tích Lịch Sử",
    "rating": 4.6,
    "rating_count": 1250,
    "similarity": 0.95,
    "distance_km": 0.5,
    "distance_m": 500,
    "images": [
      {"id": "uuid", "url": "https://..."}
    ]
  }
]
```

---

### 5. GET /api/places/{place_id}

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

### 6. POST /api/places

Tạo địa điểm mới.

**Authentication:** Requires JWT token (Bearer)

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

### 7. PUT /api/places/{place_id}

Cập nhật địa điểm.

**Authentication:** Requires JWT token (Bearer)

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

### 8. DELETE /api/places/{place_id}

Xóa địa điểm.

**Authentication:** Requires JWT token (Bearer)

> ⚠️ Trigger `trigger_delete_place_cascade` tự động xóa images và comments liên quan.

**Response:**
```json
{
  "message": "Đã xóa địa điểm thành công",
  "id": "uuid"
}
```

---

### 9. GET /api/places/{place_id}/images

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

### 10. GET /api/places/{place_id}/comments

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

**Authentication:** Requires JWT token (Bearer)

> ✅ User ID được lấy từ JWT token. Tự động tạo guest user nếu `user_id` không tồn tại trong database.

**Request Body:**
```json
{
  "place_id": "uuid",
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

**Authentication:** Requires JWT token (Bearer)

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

**Authentication:** Requires JWT token (Bearer)

> ⚠️ Trigger `trigger_update_place_rating` tự động cập nhật rating của place.

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

**Authentication:** Requires JWT token (Bearer)

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

**Authentication:** Requires JWT token (Bearer)

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

### 1. GET /api/comments/{comment_id}/images

Lấy danh sách hình ảnh của một comment.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `comment_id` | uuid | ID của comment |

**Response:**
```json
[
  {
    "id": "uuid",
    "url": "https://storage.supabase.co/...",
    "place_id": "uuid",
    "comment_id": "uuid",
    "is_scraped": false,
    "uploaded_at": "2024-01-01T00:00:00"
  }
]
```

---

### 2. POST /api/upload

Upload ảnh lên Supabase Storage.

**Authentication:** Requires JWT token (Bearer)

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

## Chat (AI Chatbot)

### 1. POST /api/chat

Main chat endpoint cho chatbot AI sử dụng Gemini.

**Authentication:** Optional JWT token (Bearer) - Cho phép personalized recommendations nếu có token.

**Request Body:**
```json
{
  "message": "Tìm quán cafe gần đây",
  "session_id": "optional-session-id",
  "user_lat": 10.7769,
  "user_lon": 106.7009
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | ✅ Yes | Câu hỏi/yêu cầu của user |
| `session_id` | string | No | Session identifier (optional) |
| `user_lat` | float | No | Latitude của user (optional) |
| `user_lon` | float | No | Longitude của user (optional) |

**Response:**
```json
{
  "answer": "Dưới đây là các quán cafe gần bạn...",
  "places": [
    {
      "id": "uuid",
      "name": "Cafe ABC",
      "address": "...",
      "rating": 4.5,
      "distance_km": 0.5
    }
  ],
  "query_type": "nearby_search",
  "total_places": 5,
  "user_location": {
    "lat": 10.7769,
    "lon": 106.7009
  }
}
```

---

### 2. GET /api/chat/config

Lấy cấu hình chat hiện tại (non-sensitive data).

**Response:**
```json
{
  "default_nearby_radius_km": 5.0,
  "default_nearby_radius_km_short": 2.0,
  "top_n_semantic_results": 30,
  "top_k_final_results": 10,
  "weights": {
    "semantic": 0.3,
    "distance": 0.3,
    "rating": 0.2,
    "popularity": 0.2
  }
}
```

---

### 3. POST /api/chat/itinerary/save

Lưu itinerary cho một session.

**Authentication:** Optional JWT token (Bearer)

**Request Body:**
```json
{
  "session_id": "session-123",
  "title": "Hành trình 3 ngày tại Hà Nội",
  "content": "Chi tiết lịch trình...",
  "places": ["place-id-1", "place-id-2"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Itinerary saved successfully",
  "itinerary_id": 1
}
```

---

### 4. GET /api/chat/itinerary/list/{session_id}

Lấy tất cả itineraries cho một session.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | ID của session |

**Response:**
```json
{
  "success": true,
  "itineraries": [
    {
      "id": 1,
      "title": "Hành trình 3 ngày tại Hà Nội",
      "content": "Chi tiết lịch trình...",
      "places": ["place-id-1", "place-id-2"],
      "created_at": null
    }
  ]
}
```

---

## Itinerary

### POST /api/itinerary/generate

Tạo lịch trình du lịch tự động dựa trên destination và preferences.

**Request Body:**
```json
{
  "destination": "Hồ Chí Minh",
  "num_days": 3,
  "preferences": ["ẩm thực", "văn hóa"],
  "budget": "medium",
  "start_time": "08:00",
  "end_time": "22:00"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `destination` | string | ✅ Yes | - | Địa điểm du lịch |
| `num_days` | int | ✅ Yes | - | Số ngày du lịch |
| `preferences` | string[] | No | [] | Sở thích (ẩm thực, văn hóa, ...) |
| `budget` | string | No | "medium" | Mức ngân sách (low/medium/high) |
| `start_time` | string | No | "08:00" | Giờ bắt đầu mỗi ngày |
| `end_time` | string | No | "22:00" | Giờ kết thúc mỗi ngày |

**Response:**
```json
{
  "destination": "Hồ Chí Minh",
  "num_days": 3,
  "itinerary": {
    "day_1": [
      {
        "time": "08:00",
        "place": "Chợ Bến Thành",
        "description": "Khám phá chợ truyền thống",
        "duration": 120
      }
    ],
    "day_2": [...],
    "day_3": [...]
  }
}
```

---

## Text-to-Speech

### 1. POST /api/tts

Convert text to speech using Google Cloud Text-to-Speech API.

**Authentication:** No (Public endpoint)

**Request Body:**
```json
{
  "text": "Xin chào, chào mừng bạn đến Việt Nam!",
  "language": "vi-VN"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `text` | string | ✅ Yes | - | Text to convert to speech (1-5000 characters) |
| `language` | string | No | "vi-VN" | Language code (vi-VN, en-US, ja-JP, zh-CN, ko-KR) |

**Supported Languages:**
- `vi-VN`: Vietnamese (Tiếng Việt)
- `en-US`: English (United States)
- `ja-JP`: Japanese (日本語)
- `zh-CN`: Chinese Mandarin (中文)
- `ko-KR`: Korean (한국어)

**Response:**
- Content-Type: `audio/mpeg`
- Returns MP3 audio file with female voice
- Can be played directly in browser or downloaded

**Example (cURL):**
```bash
curl -X POST "http://localhost:8000/api/tts" \
  -H "Content-Type: application/json" \
  -d '{"text": "Xin chào, chào mừng bạn đến Việt Nam!", "language": "vi-VN"}' \
  --output welcome.mp3
```

**Example (JavaScript):**
```javascript
const response = await fetch('/api/tts', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    text: "Xin chào, chào mừng bạn đến Việt Nam!",
    language: "vi-VN"
  })
});

const blob = await response.blob();
const audio = new Audio(URL.createObjectURL(blob));
audio.play();
```

**Error Responses:**

400 - Unsupported Language:
```json
{
  "detail": "Ngôn ngữ không được hỗ trợ: fr-FR. Các ngôn ngữ hỗ trợ: en-US, ja-JP, ko-KR, vi-VN, zh-CN"
}
```

422 - Validation Error:
```json
{
  "detail": [
    {
      "loc": ["body", "text"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

500 - TTS Service Error:
```json
{
  "detail": "Lỗi khi chuyển đổi văn bản thành giọng nói: [error details]"
}
```

---

### 2. GET /api/tts/languages

Get list of supported languages for text-to-speech.

**Authentication:** No

**Response:**
```json
{
  "supported_languages": [
    "en-US",
    "ja-JP",
    "ko-KR",
    "vi-VN",
    "zh-CN"
  ],
  "details": {
    "vi-VN": {
      "name": "Vietnamese",
      "native_name": "Tiếng Việt",
      "voice": "vi-VN-Wavenet-A"
    },
    "en-US": {
      "name": "English (US)",
      "native_name": "English",
      "voice": "en-US-Neural2-F"
    },
    "ja-JP": {
      "name": "Japanese",
      "native_name": "日本語",
      "voice": "ja-JP-Wavenet-A"
    },
    "zh-CN": {
      "name": "Chinese (Mandarin)",
      "native_name": "中文",
      "voice": "cmn-CN-Wavenet-A"
    },
    "ko-KR": {
      "name": "Korean",
      "native_name": "한국어",
      "voice": "ko-KR-Wavenet-A"
    }
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/tts/languages
```

---

## Authentication

API sử dụng JWT (JSON Web Token) để xác thực user.

### Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes* | Bearer token: `Bearer <JWT_TOKEN>` (bắt buộc cho các endpoint cần xác thực) |

### JWT Token Format

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Endpoints yêu cầu JWT Authentication:**
- `POST /api/places` - Tạo địa điểm mới
- `PUT /api/places/{id}` - Cập nhật địa điểm
- `DELETE /api/places/{id}` - Xóa địa điểm
- `POST /api/comments` - Tạo comment mới
- `PUT /api/comments/{id}` - Cập nhật comment
- `DELETE /api/comments/{id}` - Xóa comment
- `POST /api/comments/{id}/images` - Thêm ảnh vào comment
- `DELETE /api/comments/{id}/images/{img_id}` - Xóa ảnh khỏi comment
- `POST /api/upload` - Upload ảnh

**Endpoints hỗ trợ Optional JWT (cho personalization):**
- `POST /api/chat` - Chat với AI chatbot
- `POST /api/chat/itinerary/save` - Lưu itinerary

> 📝 Để biết thêm chi tiết về JWT authentication, xem [JWT_AUTHENTICATION_GUIDE.md](JWT_AUTHENTICATION_GUIDE.md)

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
| **Health & Info** |
| 1 | GET | `/health` | No | Health check |
| 2 | GET | `/` | No | API info |
| **Places** |
| 3 | GET | `/api/places` | No | Lấy danh sách places với filters |
| 4 | GET | `/api/places/search` | No | Tìm kiếm địa điểm theo tên (fuzzy search) |
| 5 | GET | `/api/places/nearby` | No | Lấy places gần vị trí user |
| 6 | GET | `/api/places/categories` | No | Lấy danh sách categories |
| 7 | GET | `/api/places/{id}` | No | Lấy chi tiết place |
| 8 | POST | `/api/places` | **JWT** | Tạo place mới |
| 9 | PUT | `/api/places/{id}` | **JWT** | Cập nhật place |
| 10 | DELETE | `/api/places/{id}` | **JWT** | Xóa place |
| 11 | GET | `/api/places/{id}/images` | No | Lấy ảnh của place |
| 12 | GET | `/api/places/{id}/comments` | No | Lấy comments của place |
| **Comments** |
| 13 | POST | `/api/comments` | **JWT** | Tạo comment mới |
| 14 | PUT | `/api/comments/{id}` | **JWT** | Cập nhật comment (owner only) |
| 15 | DELETE | `/api/comments/{id}` | **JWT** | Xóa comment (owner only) |
| 16 | POST | `/api/comments/{id}/images` | **JWT** | Thêm ảnh vào comment |
| 17 | DELETE | `/api/comments/{id}/images/{img_id}` | **JWT** | Xóa ảnh khỏi comment |
| **Images** |
| 18 | GET | `/api/comments/{id}/images` | No | Lấy ảnh của comment |
| 19 | POST | `/api/upload` | **JWT** | Upload ảnh lên storage |
| **Users** |
| 20 | GET | `/api/users/{id}/comments` | No | Lấy tất cả comments của user |
| 21 | GET | `/api/users/{id}/commented-places` | No | Lấy places user đã comment |
| **Chat (AI Chatbot)** |
| 22 | POST | `/api/chat` | Optional JWT | Chat với AI chatbot |
| 23 | GET | `/api/chat/config` | No | Lấy cấu hình chat |
| 24 | POST | `/api/chat/itinerary/save` | Optional JWT | Lưu itinerary |
| 25 | GET | `/api/chat/itinerary/list/{session_id}` | No | Lấy danh sách itineraries |
| **Itinerary** |
| 26 | POST | `/api/itinerary/generate` | No | Tạo lịch trình du lịch tự động |
| **Text-to-Speech** |
| 27 | POST | `/api/tts` | No | Convert text to speech (MP3) |
| 28 | GET | `/api/tts/languages` | No | Lấy danh sách ngôn ngữ hỗ trợ |

---

## Notes

1. **Authentication**: API sử dụng JWT Bearer token cho authentication. Xem [JWT_AUTHENTICATION_GUIDE.md](JWT_AUTHENTICATION_GUIDE.md) để biết thêm chi tiết.

2. **Images Workflow**: Upload ảnh trước qua `/api/upload`, sau đó dùng URLs trả về khi tạo/update comment.

3. **Distance Calculation**: Khi truyền `lat`, `lon`, API sẽ tính `distance_km` và `distance_m` cho mỗi place sử dụng PostGIS.

4. **Fuzzy Search**: Endpoint `/api/places/search` sử dụng PostgreSQL similarity để tìm kiếm địa điểm theo tên với độ tương đồng >= 50%.

5. **Guest User**: Khi tạo comment mà `user_id` không tồn tại, RPC sẽ tự động tạo guest user.

6. **Coordinates Format**: Database lưu coordinates dạng GeoJSON `[lon, lat]` array.

7. **Rating Auto-Update**: Khi thêm/sửa/xóa comment, trigger `trigger_update_place_rating` sẽ tự động cập nhật rating trung bình của place.

8. **AI Chatbot**: Endpoint `/api/chat` sử dụng Gemini AI để xử lý natural language queries và đề xuất địa điểm dựa trên semantic search.

9. **Itinerary Generation**: Endpoint `/api/itinerary/generate` tự động tạo lịch trình du lịch dựa trên preferences và constraints của user.

10. **Text-to-Speech**: Endpoint `/api/tts` sử dụng Google Cloud Text-to-Speech API để chuyển đổi văn bản thành giọng nói MP3, hỗ trợ 5 ngôn ngữ (Vietnamese, English, Japanese, Chinese, Korean) với giọng nữ.

---

## Changelog

### Version 1.2.0 (Latest)
- ✅ Thêm Text-to-Speech endpoints:
  - `POST /api/tts` - Convert text to speech (MP3)
  - `GET /api/tts/languages` - Lấy danh sách ngôn ngữ hỗ trợ
- ✅ Hỗ trợ 5 ngôn ngữ: Vietnamese, English, Japanese, Chinese, Korean
- ✅ Sử dụng Google Cloud Text-to-Speech API với giọng nữ chất lượng cao

### Version 1.1.0
- ✅ Thêm JWT Authentication cho tất cả endpoints cần xác thực
- ✅ Thêm endpoint `/api/places/search` - Fuzzy search theo tên địa điểm
- ✅ Thêm endpoint `/api/comments/{comment_id}/images` - Lấy ảnh của comment
- ✅ Thêm AI Chat endpoints:
  - `POST /api/chat` - Main chat endpoint
  - `GET /api/chat/config` - Lấy cấu hình
  - `POST /api/chat/itinerary/save` - Lưu itinerary
  - `GET /api/chat/itinerary/list/{session_id}` - Danh sách itineraries
- ✅ Thêm Itinerary endpoint:
  - `POST /api/itinerary/generate` - Tạo lịch trình tự động
- ✅ Cập nhật documentation với format chuẩn và chi tiết hơn

### Version 1.0.0
- Initial release với basic CRUD operations cho Places, Comments, Users, Images
