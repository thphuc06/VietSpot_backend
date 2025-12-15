from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class PlaceBase(BaseModel):
    """Base Place schema with common attributes."""
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PlaceCreate(PlaceBase):
    """Schema for creating a new Place."""
    pass


class PlaceUpdate(PlaceBase):
    """Schema for updating a Place."""
    name: Optional[str] = None


class PlaceInDB(PlaceBase):
    """Schema for Place as stored in database."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class Place(PlaceInDB):
    """Schema for Place in API responses."""
    pass
