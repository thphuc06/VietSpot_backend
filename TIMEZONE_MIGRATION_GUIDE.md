# Timezone Migration Guide - VietSpot Backend

## Tổng Quan

Migration này sửa vấn đề timezone handling trong backend để:
- Lưu timestamps trong database với timezone-aware format (TIMESTAMPTZ)
- Trả về timestamps trong API responses với múi giờ Việt Nam (UTC+7)
- Sử dụng format ISO 8601 chuẩn với timezone indicator

## Các Thay Đổi Đã Thực Hiện

### 1. Database Schema Changes
- `comments.date`: TIMESTAMP → TIMESTAMPTZ
- `images.uploaded_at`: TIMESTAMP → TIMESTAMPTZ

### 2. Backend Code Changes
- **Thêm mới**: `app/core/datetime_utils.py` - Timezone utilities
- **Cập nhật**: `app/core/config.py` - Thêm timezone settings
- **Cập nhật**: `app/schemas/comment.py` - Field serializer cho date
- **Cập nhật**: `app/schemas/image.py` - Field serializer cho uploaded_at
- **Cập nhật**: `app/schemas/place.py` - Field serializer cho created_at
- **Cập nhật**: `app/api/endpoints/comments.py:230` - Fix naive datetime
- **Cập nhật**: `main.py:45` - Fix health check timestamp

### 3. API Response Format Changes

**Trước:**
```json
{
  "date": "2024-01-15",
  "uploaded_at": "2024-01-15T03:30:45.123456"
}
```

**Sau:**
```json
{
  "date": "2024-01-15T10:30:45+07:00",
  "uploaded_at": "2024-01-15T10:30:45+07:00"
}
```

## Hướng Dẫn Deployment

### Bước 1: Backup Database (QUAN TRỌNG!)

Trước khi bắt đầu, **BẮT BUỘC** phải backup database:

1. Vào Supabase Dashboard
2. Chọn project của bạn
3. Settings → Database → Backup
4. Hoặc export tables: `comments`, `images`, `places`

### Bước 2: Run Database Migration

1. Mở Supabase SQL Editor
2. Copy toàn bộ nội dung file `alembic/versions/001_convert_comments_date_to_timestamptz.sql`
3. Paste vào SQL Editor
4. Click "Run"
5. Kiểm tra output - phải thấy message "Migration successful!"

**Verify migration thành công:**
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name IN ('comments', 'images')
  AND column_name IN ('date', 'uploaded_at')
ORDER BY table_name, column_name;
```

Kết quả mong đợi:
| table_name | column_name  | data_type                    |
|-----------|--------------|------------------------------|
| comments  | date         | timestamp with time zone     |
| images    | uploaded_at  | timestamp with time zone     |

### Bước 3: Deploy Backend Code

**Nếu đang chạy local:**
```bash
cd c:\HCMUS\ComputationalThinking\fastapi\VietSpot_backend

# Stop server (Ctrl+C)

# Restart server
python main.py
# Hoặc
uvicorn main:app --reload
```

**Nếu deploy trên server:**
```bash
# Pull latest code
git pull origin main

# Restart service
systemctl restart vietspot-backend
# Hoặc
pm2 restart vietspot-backend
```

### Bước 4: Verify API Responses

**Test 1: Health Check**
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45+07:00",  // ← Phải có +07:00
  "version": "1.0.0"
}
```

**Test 2: Get Comments**
```bash
curl http://localhost:8000/api/places/{place_id}/comments
```

Expected response:
```json
[
  {
    "id": "uuid",
    "place_id": "uuid",
    "date": "2024-01-15T10:30:45+07:00",  // ← Phải có +07:00
    "images": [
      {
        "id": "uuid",
        "uploaded_at": "2024-01-15T10:30:45+07:00"  // ← Phải có +07:00
      }
    ]
  }
]
```

**Test 3: Create Comment (cần JWT token)**
```bash
curl -X POST http://localhost:8000/api/comments \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "place_id": "your-place-id",
    "author_name": "Test User",
    "rating": 5,
    "text": "Great place!",
    "image_urls": []
  }'
```

Sau đó kiểm tra lại comment vừa tạo để verify `date` field.

## Troubleshooting

### Lỗi: "VIETNAM_TZ not found" hoặc "ZoneInfo error"

**Nguyên nhân**: Python thiếu timezone database

**Giải pháp**:
```bash
# Windows
pip install tzdata

# Linux/Mac (should work by default)
# If not, install:
sudo apt-get install tzdata  # Ubuntu/Debian
```

### Lỗi: "Module 'app.core.datetime_utils' not found"

**Nguyên nhân**: File mới chưa được load

**Giải pháp**:
```bash
# Restart Python process
# Kiểm tra file tồn tại:
ls app/core/datetime_utils.py
```

### Timestamps vẫn không có timezone (+07:00)

**Nguyên nhân**: Database migration chưa chạy hoặc thất bại

**Giải pháp**:
1. Verify database schema (xem Bước 2 phía trên)
2. Check logs xem có error không
3. Restart backend service

### API trả về 500 Internal Server Error

**Nguyên nhân**: Có lỗi trong code hoặc Pydantic serialization

**Giải pháp**:
```bash
# Check logs
tail -f logs/app.log  # Linux
# Hoặc xem console output khi chạy local

# Common issue: circular import
# Solution: Restart app completely
```

## Rollback Plan

Nếu có vấn đề nghiêm trọng, rollback như sau:

### Rollback Database
```sql
BEGIN;

-- Rollback comments.date
ALTER TABLE comments ADD COLUMN date_old TIMESTAMP;
UPDATE comments SET date_old = date::TIMESTAMP WHERE date IS NOT NULL;
ALTER TABLE comments DROP COLUMN date;
ALTER TABLE comments RENAME COLUMN date_old TO date;

-- Rollback images.uploaded_at
ALTER TABLE images ADD COLUMN uploaded_at_old TIMESTAMP;
UPDATE images SET uploaded_at_old = uploaded_at::TIMESTAMP WHERE uploaded_at IS NOT NULL;
ALTER TABLE images DROP COLUMN uploaded_at;
ALTER TABLE images RENAME COLUMN uploaded_at_old TO uploaded_at;

COMMIT;
```

### Rollback Backend Code
```bash
git revert HEAD
# Hoặc
git checkout <commit-hash-trước-migration>

# Restart service
```

## Checklist Deployment

- [ ] **Pre-deployment**
  - [ ] Backup database
  - [ ] Test migration trên database test/staging
  - [ ] Review tất cả code changes
  - [ ] Thông báo downtime (nếu cần)

- [ ] **Deployment**
  - [ ] Run database migration
  - [ ] Verify migration success
  - [ ] Deploy backend code
  - [ ] Restart backend service

- [ ] **Post-deployment**
  - [ ] Test health check endpoint
  - [ ] Test GET comments endpoint
  - [ ] Test POST comment endpoint (với auth)
  - [ ] Test POST images endpoint (với auth)
  - [ ] Check logs for errors
  - [ ] Monitor error rates

- [ ] **24h Post-deployment**
  - [ ] Review logs
  - [ ] Check user feedback
  - [ ] Monitor performance metrics
  - [ ] Update frontend nếu cần

## Technical Details

### Timezone Handling Strategy

1. **Storage Layer (Database)**
   - All timestamps stored in UTC
   - Use TIMESTAMPTZ type
   - PostgreSQL `NOW()` returns UTC by default

2. **Application Layer (Backend)**
   - All datetime operations use timezone-aware objects
   - Use `get_utc_now()` instead of `datetime.now()`
   - Never use naive datetimes

3. **API Layer (Response)**
   - Pydantic `field_serializer` converts UTC → UTC+7
   - Format: ISO 8601 with timezone (`+07:00`)
   - Automatic conversion in schema layer

### Timezone Utilities Functions

```python
from app.core.datetime_utils import (
    get_utc_now,           # Get current UTC time
    get_vietnam_now,       # Get current Vietnam time
    to_vietnam_time,       # Convert any datetime to UTC+7
    format_iso8601_vietnam # Format as ISO 8601 with +07:00
)
```

### Example Usage

```python
# ❌ BAD: Naive datetime
datetime.now().isoformat()  # "2024-01-15T10:30:45.123456"

# ✅ GOOD: Timezone-aware
get_utc_now().isoformat()  # "2024-01-15T03:30:45+00:00"

# ✅ GOOD: Vietnam timezone for display
format_iso8601_vietnam(get_utc_now())  # "2024-01-15T10:30:45+07:00"
```

## Questions?

Nếu có vấn đề hoặc câu hỏi:
1. Check logs: `tail -f logs/app.log`
2. Verify database schema đã được update
3. Restart backend service
4. Check this guide's Troubleshooting section

## References

- ISO 8601: https://en.wikipedia.org/wiki/ISO_8601
- PostgreSQL TIMESTAMPTZ: https://www.postgresql.org/docs/current/datatype-datetime.html
- Python zoneinfo: https://docs.python.org/3/library/zoneinfo.html
- Pydantic field_serializer: https://docs.pydantic.dev/latest/concepts/serialization/
