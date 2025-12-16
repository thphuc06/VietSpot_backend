from fastapi import APIRouter, HTTPException
from app.schemas.itinerary import ItineraryRequest, ItineraryResponse
from app.services.itinerary_service import ItineraryService

router = APIRouter()


@router.post("/generate", response_model=ItineraryResponse)
async def generate_itinerary(request: ItineraryRequest):
    """
    Generate travel itinerary based on destination, number of days, and preferences.
    
    Example request:
    ```json
    {
        "destination": "Hồ Chí Minh",
        "num_days": 3,
        "preferences": ["ẩm thực", "văn hóa"],
        "budget": "medium",
        "start_time": "08:00",
        "end_time": "22:00"
    }
    ```
    """
    try:
        service = ItineraryService()
        itinerary = service.generate_itinerary(request)
        return itinerary
    except Exception as e:
        print(f"Error generating itinerary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate itinerary: {str(e)}")
