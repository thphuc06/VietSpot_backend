from fastapi import APIRouter
from app.api.endpoints import places

api_router = APIRouter()

# Include routers
api_router.include_router(
    places.router,
    tags=["places"]
)
