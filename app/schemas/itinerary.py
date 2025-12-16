from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import time


class ItineraryRequest(BaseModel):
    """Request model for itinerary generation"""
    destination: str = Field(..., description="Destination city/location (e.g., 'Hồ Chí Minh')")
    num_days: int = Field(..., ge=1, le=7, description="Number of days (1-7)")
    preferences: Optional[List[str]] = Field(
        default_factory=list, 
        description="User preferences (e.g., 'văn hóa', 'ẩm thực', 'thiên nhiên')"
    )
    budget: Optional[str] = Field(None, description="Budget level: 'low', 'medium', 'high'")
    max_budget: Optional[int] = Field(None, description="Maximum budget in VND (e.g., 2000000 for 2 million)")
    start_time: Optional[str] = Field("08:00", description="Daily start time (HH:MM)")
    end_time: Optional[str] = Field("22:00", description="Daily end time (HH:MM)")
    user_lat: Optional[float] = Field(None, description="User's latitude for proximity optimization")
    user_lon: Optional[float] = Field(None, description="User's longitude for proximity optimization")


class ActivityDetail(BaseModel):
    """Single activity in itinerary"""
    time: str = Field(..., description="Activity time (HH:MM)")
    duration_minutes: int = Field(..., description="Estimated duration in minutes")
    activity_type: str = Field(..., description="Type: breakfast, lunch, dinner, visit, coffee, rest")
    place_id: Optional[str] = None
    place_name: str = Field(..., description="Place name")
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rating: Optional[float] = None
    category: Optional[str] = None
    description: str = Field(..., description="Activity description")
    tips: Optional[str] = Field(None, description="Tips for this activity")
    estimated_cost: Optional[str] = Field(None, description="Estimated cost range")


class DayItinerary(BaseModel):
    """Itinerary for one day"""
    day: int = Field(..., description="Day number (1, 2, 3...)")
    date: Optional[str] = Field(None, description="Date if provided")
    theme: str = Field(..., description="Theme of the day (e.g., 'Khám phá trung tâm', 'Văn hóa lịch sử')")
    activities: List[ActivityDetail] = Field(..., description="List of activities for the day")
    total_activities: int = Field(..., description="Total number of activities")
    estimated_distance_km: Optional[float] = Field(None, description="Total travel distance")


class ItineraryResponse(BaseModel):
    """Response model for itinerary generation"""
    destination: str = Field(..., description="Destination name")
    num_days: int = Field(..., description="Number of days")
    itinerary: List[DayItinerary] = Field(..., description="Day-by-day itinerary")
    summary: str = Field(..., description="Overall trip summary")
    total_places: int = Field(..., description="Total unique places visited")
    tips: List[str] = Field(default_factory=list, description="General travel tips")
    estimated_budget: Optional[str] = Field(None, description="Estimated total budget")
