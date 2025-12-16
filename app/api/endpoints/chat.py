from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from app.services.orchestrator import ChatbotOrchestrator
from app.api.deps import get_optional_user_id
from app.schemas.chat import (
    ChatRequest, 
    ChatResponse, 
    ItinerarySaveRequest, 
    ItinerarySaveResponse,
    ItineraryListResponse
)
from app.core.config import settings

router = APIRouter(prefix="/chat", tags=["Chat"])

# Initialize orchestrator
orchestrator = ChatbotOrchestrator()

# In-memory storage for itineraries (replace with database in production)
itineraries_db = {}


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user_id: Optional[str] = Depends(get_optional_user_id)
):
    """
    Main chat endpoint
    
    Parameters:
    - message: User's query/prompt
    - session_id: Session identifier (optional)
    - user_lat: User's latitude (optional)
    - user_lon: User's longitude (optional)
    
    Optional JWT authentication for personalized recommendations.
    
    Returns:
    - answer: Generated response from Gemini
    - places: List of recommended places
    - query_type: Type of query processed
    - total_places: Number of places found
    - user_location: User's coordinates if provided
    """
    try:
        # user_id can be used for personalized recommendations if needed
        response = await orchestrator.process_query(request)
        return response
    except Exception as e:
        print(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_chat_config():
    """
    Get current chat configuration (non-sensitive data)
    """
    return {
        "default_nearby_radius_km": settings.DEFAULT_NEARBY_RADIUS_KM,
        "default_nearby_radius_km_short": settings.DEFAULT_NEARBY_RADIUS_KM_SHORT,
        "top_n_semantic_results": settings.TOP_N_SEMANTIC_RESULTS,
        "top_k_final_results": settings.TOP_K_FINAL_RESULTS,
        "weights": {
            "semantic": settings.WEIGHT_SEMANTIC,
            "distance": settings.WEIGHT_DISTANCE,
            "rating": settings.WEIGHT_RATING,
            "popularity": settings.WEIGHT_POPULARITY
        }
    }


@router.post("/itinerary/save", response_model=ItinerarySaveResponse)
async def save_itinerary(
    request: ItinerarySaveRequest,
    user_id: Optional[str] = Depends(get_optional_user_id)
):
    """Save an itinerary for a session. Optional JWT authentication."""
    try:
        session_id = request.session_id
        title = request.title
        content = request.content
        places = request.places
        
        if session_id not in itineraries_db:
            itineraries_db[session_id] = []
        
        itinerary_id = len(itineraries_db[session_id]) + 1
        itinerary = {
            "id": itinerary_id,
            "title": title,
            "content": content,
            "places": places,
            "created_at": None
        }
        
        itineraries_db[session_id].append(itinerary)
        
        return ItinerarySaveResponse(
            success=True,
            message="Itinerary saved successfully",
            itinerary_id=itinerary_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/itinerary/list/{session_id}", response_model=ItineraryListResponse)
async def list_itineraries(session_id: str):
    """Get all itineraries for a session"""
    try:
        itineraries = itineraries_db.get(session_id, [])
        return ItineraryListResponse(
            success=True,
            itineraries=itineraries
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/query/{city}")
async def debug_query(city: str):
    """
    Debug endpoint to test Supabase query directly
    """
    try:
        from supabase import create_client
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        response = client.table('places').select('name, address').ilike('address', f'*{city}*').limit(10).execute()
        response2 = client.table('places').select('name').or_(f'address.ilike.*{city}*').limit(10).execute()
        
        return {
            "city": city,
            "direct_ilike_count": len(response.data),
            "or_query_count": len(response2.data),
            "sample_results": [p.get('name') for p in response.data[:5]],
            "supabase_url": settings.SUPABASE_URL[:30] + "..."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/nearby")
async def debug_nearby(lat: float = 10.752845, lon: float = 106.643431, radius: float = 2.0):
    """
    Debug endpoint to test nearby_places RPC function
    """
    try:
        from supabase import create_client
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        params = {
            "user_lat": lat,
            "user_lon": lon,
            "radius_km": radius,
            "result_limit": 10
        }
        
        rpc_response = client.rpc("nearby_places", params).execute()
        
        return {
            "lat": lat,
            "lon": lon,
            "radius_km": radius,
            "rpc_result_count": len(rpc_response.data) if rpc_response.data else 0,
            "sample_results": [p.get('name') for p in (rpc_response.data or [])[:5]],
            "raw_data": rpc_response.data[:2] if rpc_response.data else None
        }
    except Exception as e:
        return {"error": str(e), "lat": lat, "lon": lon, "radius_km": radius}
