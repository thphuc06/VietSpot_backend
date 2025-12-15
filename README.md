# VietSpot Backend

FastAPI backend for VietSpot application - Khám phá địa điểm du lịch Việt Nam.

## 🚀 Tech Stack

- **FastAPI** - Modern async web framework
- **Python 3.10+** - Latest Python features
- **Supabase** - Database & Storage (PostgreSQL + File Storage)
- **Pydantic v2** - Data validation and settings
- **Docker** - Containerization

## 📁 Project Structure

```
VietSpot_backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── places.py      # Địa điểm du lịch
│   │   │   ├── comments.py    # Comments/Reviews
│   │   │   ├── images.py      # Upload/quản lý ảnh
│   │   │   └── users.py       # User management
│   │   ├── deps.py            # Dependencies (Supabase client, auth)
│   │   └── router.py          # API router configuration
│   ├── core/
│   │   └── config.py          # Settings với pydantic-settings
│   ├── schemas/
│   │   ├── place.py           # Place schemas
│   │   ├── comment.py         # Comment schemas
│   │   ├── image.py           # Image schemas
│   │   └── user.py            # User schemas
│   └── services/
│       ├── supabase_client.py # Supabase connection
│       └── storage.py         # File storage service
├── main.py                    # FastAPI entry point
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Production Docker image
├── docker-compose.yml         # Docker development
└── .env.example               # Environment template
```

## ⚡ Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/thphuc06/VietSpot_backend.git
cd VietSpot_backend
```

### 2. Setup Environment

```bash
cp .env.example .env
```

Cấu hình file `.env`:

```env
# Supabase (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_BUCKET=images

# Application
APP_NAME=VietSpot API
DEBUG=True
```

### 3. Install Dependencies

```bash
# Tạo virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install packages
pip install -r requirements.txt
```

### 4. Run Server

```bash
uvicorn main:app --reload
```

🎉 **Server chạy tại:**
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🐳 Docker

```bash
# Development
docker-compose up -d

# Production build
docker build -t vietspot-backend .
docker run -p 8000:8000 --env-file .env vietspot-backend
```

## 📚 API Endpoints

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/health` | Health check |

### Places
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/places` | Lấy danh sách địa điểm |
| GET | `/api/places/{id}` | Chi tiết địa điểm |
| POST | `/api/places` | Tạo địa điểm mới |
| PUT | `/api/places/{id}` | Cập nhật địa điểm |
| DELETE | `/api/places/{id}` | Xóa địa điểm |

### Comments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/comments/places/{place_id}/comments` | Lấy comments của địa điểm |
| POST | `/api/comments` | Tạo comment mới |
| PUT | `/api/comments/{id}` | Cập nhật comment |
| DELETE | `/api/comments/{id}` | Xóa comment |

### Images
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/images/upload` | Upload ảnh |
| DELETE | `/api/images/{id}` | Xóa ảnh |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/{id}` | Lấy thông tin user |
| POST | `/api/users` | Tạo user |

## 📝 Example Requests

```bash
# Tạo địa điểm mới
curl -X POST "http://localhost:8000/api/places" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Vịnh Hạ Long",
    "description": "Di sản thiên nhiên thế giới UNESCO",
    "address": "Quảng Ninh",
    "city": "Hạ Long",
    "latitude": 20.9101,
    "longitude": 107.1839
  }'

# Lấy danh sách địa điểm
curl "http://localhost:8000/api/places?limit=10&city=Hạ Long"

# Lấy chi tiết địa điểm
curl "http://localhost:8000/api/places/uuid-here"
```

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPABASE_URL` | ✅ | - | Supabase project URL |
| `SUPABASE_KEY` | ✅ | - | Supabase anon/service key |
| `SUPABASE_BUCKET` | ❌ | `images` | Storage bucket name |
| `APP_NAME` | ❌ | `VietSpot API` | Application name |
| `DEBUG` | ❌ | `False` | Debug mode |
| `API_V1_PREFIX` | ❌ | `/api` | API prefix |
| `CORS_ORIGINS` | ❌ | `["*"]` | Allowed origins |

### CORS

Cấu hình trong `app/core/config.py`:

```python
CORS_ORIGINS: list[str] = [
    "http://localhost:3000",      # React dev
    "https://your-frontend.com",  # Production
]
```

## 🚀 Deploy

### Railway (Recommended)

1. Push code lên GitHub
2. Vào [railway.app](https://railway.app)
3. New Project → Deploy from GitHub
4. Add Environment Variables
5. Deploy!

### Render

1. Push code lên GitHub
2. Vào [render.com](https://render.com)
3. New → Web Service
4. Connect GitHub repo
5. Add Environment Variables
6. Deploy!

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure `CORS_ORIGINS` với domain thật
- [ ] Sử dụng Supabase service role key cho backend
- [ ] Enable HTTPS
- [ ] Setup monitoring/logging

## 📄 License

MIT

## 🤝 Contributing

Pull requests are welcome!

