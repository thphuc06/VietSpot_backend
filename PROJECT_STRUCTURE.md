# VietSpot Backend - Complete Structure

## Directory Tree

```
VietSpot_backend/
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore file
├── Dockerfile                   # Production Docker image
├── docker-compose.yml           # Local development with Docker
├── README.md                    # Complete documentation
├── requirements.txt             # Python dependencies
├── main.py                      # FastAPI application entry point
├── alembic.ini                  # Alembic configuration
├── alembic/
│   ├── README                   # Alembic readme
│   ├── env.py                   # Alembic environment (configured for async)
│   ├── script.py.mako          # Migration template
│   └── versions/                # Database migrations
└── app/
    ├── __init__.py
    ├── api/
    │   ├── __init__.py
    │   ├── router.py            # API router configuration
    │   └── endpoints/
    │       ├── __init__.py
    │       └── places.py        # Places endpoints (GET /places)
    ├── core/
    │   ├── __init__.py
    │   └── config.py            # Settings with pydantic-settings
    ├── db/
    │   ├── __init__.py
    │   └── session.py           # AsyncSession configuration
    ├── models/
    │   ├── __init__.py
    │   └── place.py             # Place model (demo)
    └── schemas/
        ├── __init__.py
        └── place.py             # Pydantic schemas (v2)
```

## Key Files Content

### requirements.txt
```
# FastAPI
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
SQLAlchemy==2.0.25
alembic==1.13.1
asyncpg==0.29.0

# Pydantic
pydantic==2.5.3
pydantic-settings==2.1.0

# Environment
python-dotenv==1.0.0

# CORS
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Testing (optional)
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
```

### app/core/config.py (Pydantic Settings)
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "VietSpot API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    DATABASE_URL: str
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    API_V1_PREFIX: str = "/api/v1"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
```

### app/db/session.py (AsyncSession Setup)
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

### main.py (FastAPI App with CORS)
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.router import api_router

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# Configure CORS (localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root():
    return {
        "message": "Welcome to VietSpot API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
```

## Features Implemented

✅ **AsyncSession Setup** - app/db/session.py with async engine and session factory
✅ **CORS Configuration** - Configured for localhost:3000 in main.py
✅ **Pydantic Settings** - app/core/config.py with pydantic-settings v2
✅ **Directory Structure** - app/{api,core,db,models,schemas}
✅ **Dockerfile** - Production-ready container image
✅ **Demo Place Model** - Complete implementation with:
   - SQLAlchemy model (app/models/place.py)
   - Pydantic schemas (app/schemas/place.py)
   - GET /api/v1/places endpoint (app/api/endpoints/places.py)
   - GET /api/v1/places/{id} endpoint
   - POST /api/v1/places endpoint
✅ **Alembic** - Configured for database migrations with async support
✅ **Docker Compose** - Local development setup with PostgreSQL
✅ **Documentation** - Comprehensive README.md

## API Endpoints

### Available Endpoints
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/v1/places` - List all places (with pagination)
- `GET /api/v1/places/{place_id}` - Get specific place
- `POST /api/v1/places` - Create new place

### Interactive Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Usage

1. **Setup Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your DATABASE_URL
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Migrations**:
   ```bash
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

4. **Start Server**:
   ```bash
   uvicorn main:app --reload
   ```

5. **Test API**:
   ```bash
   curl http://localhost:8000/api/v1/places
   ```

## Docker Usage

**Development:**
```bash
docker-compose up -d
```

**Production:**
```bash
docker build -t vietspot-backend .
docker run -p 8000:8000 --env-file .env vietspot-backend
```

## Stack Summary
- ✅ Python 3.10+
- ✅ FastAPI (async web framework)
- ✅ Async SQLAlchemy 2.0
- ✅ Supabase/PostgreSQL support (asyncpg)
- ✅ Alembic (database migrations)
- ✅ Pydantic v2 (validation & settings)
- ✅ Docker (containerization)
- ✅ CORS (localhost:3000)
