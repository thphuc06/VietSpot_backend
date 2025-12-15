from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.models.place import Place as PlaceModel
from app.schemas.place import Place, PlaceCreate

router = APIRouter()


@router.get("/places", response_model=List[Place])
async def get_places(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of places.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        db: Database session
    
    Returns:
        List of Place objects
    """
    result = await db.execute(
        select(PlaceModel)
        .offset(skip)
        .limit(limit)
    )
    places = result.scalars().all()
    return places


@router.get("/places/{place_id}", response_model=Place)
async def get_place(
    place_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific place by ID.
    
    Args:
        place_id: ID of the place to retrieve
        db: Database session
    
    Returns:
        Place object
    
    Raises:
        HTTPException: 404 if place not found
    """
    result = await db.execute(
        select(PlaceModel).where(PlaceModel.id == place_id)
    )
    place = result.scalar_one_or_none()
    
    if place is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Place with id {place_id} not found"
        )
    
    return place


@router.post("/places", response_model=Place, status_code=status.HTTP_201_CREATED)
async def create_place(
    place_in: PlaceCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new place.
    
    Args:
        place_in: Place data
        db: Database session
    
    Returns:
        Created Place object
    """
    place = PlaceModel(**place_in.model_dump())
    db.add(place)
    await db.commit()
    await db.refresh(place)
    return place
