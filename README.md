# VietSpot Backend

Production-ready FastAPI backend for VietSpot application with async SQLAlchemy, Supabase support, and Alembic migrations.

## Tech Stack

- **FastAPI** - Modern async web framework
- **Python 3.10+** - Latest Python features
- **SQLAlchemy 2.0** - Async ORM
- **Alembic** - Database migrations
- **Pydantic v2** - Data validation and settings
- **Supabase** - PostgreSQL database (or any PostgreSQL)
- **Docker** - Containerization

## Project Structure

```
VietSpot_backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   └── places.py       # Places endpoints
│   │   ├── __init__.py
│   │   └── router.py            # API router configuration
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py            # Settings with pydantic-settings
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py           # AsyncSession configuration
│   ├── models/
│   │   ├── __init__.py
│   │   └── place.py             # Place model
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── place.py             # Pydantic schemas
│   └── __init__.py
├── alembic/
│   ├── versions/                # Migration files
│   ├── env.py                   # Alembic environment
│   └── script.py.mako
├── main.py                      # FastAPI application entry point
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Production Docker image
├── docker-compose.yml           # Local development with Docker
├── alembic.ini                  # Alembic configuration
├── .env.example                 # Environment variables template
└── .gitignore

```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/thphuc06/VietSpot_backend.git
cd VietSpot_backend
```

### 2. Setup Environment

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and add your Supabase (or PostgreSQL) connection string:

```env
DATABASE_URL=postgresql+asyncpg://user:password@db.xxxxx.supabase.co:5432/postgres
```

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Run Database Migrations

```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 5. Run the Application

```bash
# Development mode
uvicorn main:app --reload

# Or using Python
python main.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Docker Deployment

### Using Docker Compose (Recommended for local development)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Using Docker Only

```bash
# Build image
docker build -t vietspot-backend .

# Run container
docker run -p 8000:8000 --env-file .env vietspot-backend
```

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check

### Places (Demo)
- `GET /api/v1/places` - List all places
  - Query params: `skip` (default: 0), `limit` (default: 100)
- `GET /api/v1/places/{place_id}` - Get specific place
- `POST /api/v1/places` - Create new place

### Example Request

```bash
# Create a place
curl -X POST "http://localhost:8000/api/v1/places" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ha Long Bay",
    "description": "UNESCO World Heritage Site",
    "address": "Quang Ninh Province",
    "city": "Ha Long",
    "latitude": 20.9101,
    "longitude": 107.1839
  }'

# Get all places
curl "http://localhost:8000/api/v1/places"
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# View current revision
alembic current
```

## Configuration

### Environment Variables

All configuration is managed through environment variables (see `.env.example`):

- `DATABASE_URL` - PostgreSQL connection string (required)
- `APP_NAME` - Application name (default: "VietSpot API")
- `APP_VERSION` - API version (default: "1.0.0")
- `DEBUG` - Debug mode (default: False)
- `API_V1_PREFIX` - API prefix (default: "/api/v1")

### CORS Configuration

CORS is configured in `main.py` to allow requests from `http://localhost:3000` (React dev server). To modify:

```python
# In app/core/config.py
CORS_ORIGINS: list[str] = ["http://localhost:3000", "https://yourdomain.com"]
```

## Development

### Adding New Models

1. Create model in `app/models/`:
```python
from sqlalchemy import Column, Integer, String
from app.db.session import Base

class YourModel(Base):
    __tablename__ = "your_table"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
```

2. Import in `app/models/__init__.py`:
```python
from app.models.your_model import YourModel
__all__ = ["YourModel"]
```

3. Create schemas in `app/schemas/your_model.py`

4. Create endpoints in `app/api/endpoints/your_model.py`

5. Register router in `app/api/router.py`

6. Generate migration:
```bash
alembic revision --autogenerate -m "Add YourModel"
alembic upgrade head
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## Production Deployment

### Using Docker

1. Build production image:
```bash
docker build -t vietspot-backend:latest .
```

2. Run with environment variables:
```bash
docker run -p 8000:8000 \
  -e DATABASE_URL="your_production_db_url" \
  -e DEBUG=False \
  vietspot-backend:latest
```

### Best Practices

- Use environment variables for all sensitive data
- Set `DEBUG=False` in production
- Use a production WSGI server (uvicorn with workers)
- Enable HTTPS/TLS
- Set up proper logging
- Use connection pooling for database
- Implement rate limiting
- Add authentication/authorization as needed

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
