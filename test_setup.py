#!/usr/bin/env python3
"""
Simple test script to verify the FastAPI application setup.
This doesn't require a database connection.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all imports work correctly."""
    print("Testing imports...")
    try:
        from app.core.config import settings
        from app.db.session import Base, get_db
        from app.models.place import Place
        from app.schemas.place import Place as PlaceSchema, PlaceCreate
        from app.api.endpoints.places import router
        from main import app
        print("✅ All imports successful!")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    try:
        from app.core.config import settings
        assert settings.APP_NAME == "VietSpot API"
        assert settings.API_V1_PREFIX == "/api/v1"
        assert "http://localhost:3000" in settings.CORS_ORIGINS
        print(f"✅ Config loaded: {settings.APP_NAME} v{settings.APP_VERSION}")
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def test_app_creation():
    """Test FastAPI app creation."""
    print("\nTesting FastAPI app...")
    try:
        from main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        assert "/" in routes
        assert "/health" in routes
        assert "/api/v1/places" in routes
        print(f"✅ FastAPI app created with {len(routes)} routes")
        return True
    except Exception as e:
        print(f"❌ App creation error: {e}")
        return False

def test_models():
    """Test SQLAlchemy models."""
    print("\nTesting SQLAlchemy models...")
    try:
        from app.models.place import Place
        from app.db.session import Base
        columns = [c.name for c in Place.__table__.columns]
        required_columns = ['id', 'name', 'city', 'latitude', 'longitude']
        for col in required_columns:
            assert col in columns, f"Missing column: {col}"
        print(f"✅ Place model has {len(columns)} columns")
        return True
    except Exception as e:
        print(f"❌ Model error: {e}")
        return False

def test_schemas():
    """Test Pydantic schemas."""
    print("\nTesting Pydantic schemas...")
    try:
        from app.schemas.place import PlaceCreate
        from datetime import datetime
        
        place = PlaceCreate(
            name="Test Place",
            description="Test Description",
            city="Test City",
            latitude=10.0,
            longitude=20.0
        )
        assert place.name == "Test Place"
        assert place.city == "Test City"
        print("✅ Pydantic schemas working correctly")
        return True
    except Exception as e:
        print(f"❌ Schema error: {e}")
        return False

def test_openapi():
    """Test OpenAPI schema generation."""
    print("\nTesting OpenAPI schema...")
    try:
        from main import app
        openapi = app.openapi()
        assert openapi["info"]["title"] == "VietSpot API"
        assert "/api/v1/places" in openapi["paths"]
        print("✅ OpenAPI schema generated successfully")
        return True
    except Exception as e:
        print(f"❌ OpenAPI error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("VietSpot Backend - Application Test Suite")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_config,
        test_app_creation,
        test_models,
        test_schemas,
        test_openapi,
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("\n🎉 All tests passed! The application is ready to use.")
        print("\nNext steps:")
        print("1. Set up your DATABASE_URL in .env file")
        print("2. Run: alembic revision --autogenerate -m 'Initial migration'")
        print("3. Run: alembic upgrade head")
        print("4. Run: uvicorn main:app --reload")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
