from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., description="User's message/prompt")
    session_id: str = Field(default="user123", description="Session identifier")
    user_lat: Optional[float] = Field(None, description="User's latitude")
    user_lon: Optional[float] = Field(None, description="User's longitude")


class PlaceInfo(BaseModel):
    """Place information in chat response"""
    place_id: str
    name: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    phone: Optional[str] = None
    website: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    opening_hours: Optional[str] = None
    about: Optional[str] = None
    distance_km: Optional[float] = None
    weather: Optional[Dict[str, Any]] = None
    score: Optional[float] = None
    images: Optional[List[str]] = Field(default_factory=list, description="List of image URLs")


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    answer: str = Field(..., description="Gemini's generated answer")
    places: List[PlaceInfo] = Field(default_factory=list, description="Recommended places")
    query_type: str = Field(..., description="Type of query: general, nearby, specific, itinerary")
    total_places: int = Field(default=0, description="Total number of places found")
    user_location: Optional[Dict[str, float]] = None
    itinerary: Optional[Dict[str, Any]] = Field(None, description="Generated itinerary if query_type is itinerary")


class QueryClassification(BaseModel):
    """Classification result from Gemini"""
    query_type: str = Field(..., description="general_query, nearby_search, specific_search, itinerary_request")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords - should be location names for search")
    keyword_variants: List[str] = Field(default_factory=list, description="All variants of keywords for better search matching")
    location_mentioned: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    price_range: Optional[str] = None
    budget_amount: Optional[int] = Field(None, description="Budget amount in VND (e.g., 2000000 for 2 million)")
    category: Optional[str] = None
    radius_km: Optional[float] = None
    number_of_places: Optional[int] = None
    num_days: Optional[int] = Field(None, description="Number of days for itinerary request")
    min_rating: Optional[float] = None
    max_rating: Optional[float] = None
    needs_semantic_search: bool = Field(default=False, description="True if query has contextual meaning requiring semantic search")
    vietnamese_query: str = Field(..., description="Query translated to Vietnamese")
    corrected_query: str = Field(..., description="Spell-checked and corrected query")
    original_language: str = Field(default="vi", description="Original language of user query: vi, en, etc.")


class ItinerarySaveRequest(BaseModel):
    """Request model for saving itinerary"""
    session_id: str = Field(default="user123", description="Session identifier")
    title: str = Field(default="Untitled Itinerary", description="Itinerary title")
    content: str = Field(default="", description="Itinerary content")
    places: List[Dict[str, Any]] = Field(default_factory=list, description="List of places")


class ItinerarySaveResponse(BaseModel):
    """Response model for saving itinerary"""
    success: bool
    message: str
    itinerary_id: int


class ItineraryListResponse(BaseModel):
    """Response model for listing itineraries"""
    success: bool
    itineraries: List[Dict[str, Any]]
