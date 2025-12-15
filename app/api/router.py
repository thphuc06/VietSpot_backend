from fastapi import APIRouter
from app.api.endpoints import places, comments, images, users, chat

api_router = APIRouter()

# Include routers
api_router.include_router(
    places.router,
    prefix="/places",
    tags=["Places"]
)

# Comments - routes đã có full path /places/{id}/comments
api_router.include_router(
    comments.router,
    prefix="",
    tags=["Comments"]
)

# Images - routes đã có full path /places/{id}/images, /images/upload
api_router.include_router(
    images.router,
    prefix="",
    tags=["Images"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

# Chat - AI chatbot endpoints
api_router.include_router(
    chat.router,
    tags=["Chat"]
)
